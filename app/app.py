# Requirements
from flask_lambda import FlaskLambda
from flask import request, render_template, url_for, Markup
import uuid
import sys
import os
import json

# Individual imports
from database.db import table, update_db_item, float_to_decimal, decimal_to_float
from bace.design_optimization import get_design_tuner, get_next_design, get_conf_dict, get_objective, context
from bace.pmc_inference import pmc, sample_thetas
from bace.user_config import answers, design_params, theta_params, likelihood_pdf, author, size_thetas, conf_dict, max_opt_time
from bace.user_convert import add_to_profile, convert_design
from bace.user_survey import nquestions, display_estimates
from static.style import css_style

from decimal import Decimal
import json

# Specify application
app = FlaskLambda(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    print(response)
    return response

# Add file path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Homepage to check that Lambda application is up and running
@app.route('/')
def homepage():
    return format_response({ 'message': 'Hello! Your BACE application is up and running.', 'author': f"{author or 'Update author in bace/user_config.py'}"})

context.max_opt_time = max_opt_time

# Return a random design
@app.route('/random_design', methods=['GET'])
def random_design():
    conf_dict_earlystop = get_conf_dict(conf_dict)
    objective = get_objective(answers, likelihood_pdf)
    design_tuner = get_design_tuner(design_params, objective, conf_dict_earlystop)
    design = design_tuner.ds.get_random_sample(size=1)[0]
    return format_response(design)

# Create a new profile in the database
@app.route('/create_profile', methods=['POST'])
def create_profile():

    # Store profile-specific information
    profile = get_request(request)
    profile['profile_id'] = str(uuid.uuid4()) # Create new profile_id
    profile = add_to_profile(profile)

    # Select first design
    conf_dict_earlystop = get_conf_dict(conf_dict)
    objective = get_objective(answers, likelihood_pdf)
    design_tuner = get_design_tuner(design_params, objective, conf_dict_earlystop)
    next_design = get_next_design(sample_thetas(theta_params, size_thetas), design_tuner)

    # Add next_design to design history and store placeholder for answer_history
    profile['design_history'] = [next_design]
    profile['answer_history'] = []

    # Put item into database
    table.put_item(Item=float_to_decimal(profile))
    output_design = convert_design(next_design, profile, profile)

    print(f'Successfully created profile for {profile.get("survey_id") or profile.get("profile_id")}')

    response = {
        'profile_id': profile.get('profile_id'),
        **output_design
    }

    return format_response(response)

# Update profile and return next design.
@app.route('/update_profile', methods=["POST"])
def update_profile():

    # Store profile specific information
    request_data = get_request(request)

    print(request_data)

    conf_dict_earlystop = get_conf_dict(conf_dict)
    objective = get_objective(answers, likelihood_pdf)
    design_tuner = get_design_tuner(design_params, objective, conf_dict_earlystop)

    # If profile_id is present, proceed
    if request_data.get('profile_id') != "${e://Field/profile_id}":
        # Store profile key value and answer
        key={'profile_id': request_data.get('profile_id')}
        answer=request_data.get('answer')

        # Retrieve profile from database
        profile = table.get_item(Key=key)['Item']
        profile = decimal_to_float(profile)

        if (not answer) or (answer.isspace()):
            next_design = profile['design_history'][-1]
        else:
            profile['answer_history'].append(answer)

            # Compute pmc to get posterior distribution after answer
            thetas = pmc(theta_params, profile['answer_history'], profile['design_history'], likelihood_pdf, size_thetas)

            # Compute next design
            next_design = get_next_design(thetas, design_tuner)

            # Update item
            profile['design_history'].append(next_design)

            # Store updates
            updates = {
                'design_history': profile.get('design_history'),
                'answer_history': profile.get('answer_history')
            }

            # Push changes to database
            update_db_item(table, key, updates)
    else:
        # Select random design
        next_design = design_tuner.ds.get_random_sample(size=1)[0]
        profile = dict()

    output_design = convert_design(next_design, profile, request_data)
    return format_response(output_design)

@app.route('/estimates', methods=["GET", "POST"])
def update_estimates():

    # Store profile specific information
    data = get_request(request)

    if data.get('profile_id') != "${e://Field/profile_id}":

        key={'profile_id': data.get('profile_id')}
        answer=data.get('answer')

        # Retrieve profile from database
        profile = table.get_item(Key=key)['Item']

        print('Profile from database')
        print(profile)

        if request.method == 'GET':

            estimates = profile.get('estimates')

        else:

            if (answer) and (not answer.isspace()):
                # Update item
                profile['answer_history'].append(answer)
            else:
                profile['design_history'].pop()

            profile = decimal_to_float(profile)

            # Calculate estimates
            estimates = pmc(theta_params, profile['answer_history'], profile['design_history'], likelihood_pdf, size_thetas*10, J=10)
            estimates = estimates.agg(['mean', 'median', 'std']).to_dict()

            # Store values to be updated
            updates = {
                'answer_history': profile.get('answer_history'),
                'estimates': estimates
            }

            # Push changes to database
            update_db_item(table, key, updates)

        return format_response(estimates)
    else:

        # Sample from prior distribution
        thetas = sample_thetas(theta_params, size_thetas)
        # Calculate mean and median estimates
        estimates = thetas.agg(['mean', 'median', 'std']).to_dict()
        # Return sample output
        return format_response(estimates)

@app.route('/survey', methods=["GET", "POST"])
def survey():

    css_style_markup = Markup(f'<style>{css_style}</style>')
    conf_dict_earlystop = get_conf_dict(conf_dict)
    objective = get_objective(answers, likelihood_pdf)
    design_tuner = get_design_tuner(design_params, objective, conf_dict_earlystop)

    if request.method == 'GET':
        return render_template('instructions.html', redirect_url='survey', css_style=css_style_markup)
    else:

        # Store body of request
        profile = get_request(request)
        print(profile)

        if profile.get('profile_id'):

            # Store profile specific information
            request_data = get_request(request)

            # Store profile key value
            key={'profile_id': request_data.get('profile_id')}
            answer=request_data.get('answer')

            # Retrieve profile from database
            profile = table.get_item(Key=key)['Item']
            profile = decimal_to_float(profile)
            profile['answer_history'].append(answer)
            print(profile)

            # Compute pmc to get posterior distribution after answer
            thetas = pmc(theta_params, profile['answer_history'], profile['design_history'], likelihood_pdf, size_thetas)

            if len(profile['design_history']) + 1 <= nquestions:

                # Compute next design
                next_design = get_next_design(thetas, design_tuner)

                # Update item
                profile['design_history'].append(next_design)

                # Store updates
                updates = {
                    'design_history': profile.get('design_history'),
                    'answer_history': profile.get('answer_history')
                }

                # Push changes to database
                update_db_item(table, key, updates)

                # Convert Next Design
                profile['question_number'] = 'survey'
                output_design = convert_design(next_design, profile, profile)

                inputs = {'profile_id': profile['profile_id']}

                return render_template('survey.html', output_design=output_design, inputs=inputs, question_number=len(profile.get("design_history")), nquestions=nquestions, redirect_url='survey', css_style=css_style_markup)

            else:

                estimates = thetas.agg(['mean', 'median', 'std'])

                # Store values to be updated
                updates = {
                    'answer_history': profile.get('answer_history'),
                    'estimates': estimates.to_dict()
                }

                # Push changes to database
                update_db_item(table, key, updates)

                if display_estimates:
                    # calculate the mean and median of the dataframe using agg()
                    result_df = estimates.transpose()

                    # add the parameter names as a separate column
                    result_df['Parameter'] = result_df.index

                    # reorder the columns then rename
                    result_df = result_df[['Parameter', 'mean', 'median', 'std']]
                    result_df.columns = ['Parameter', 'Mean', 'Median', 'Std']

                    # convert the dataframe into an html table
                    html_table = result_df.to_html(index=False)

                    return render_template('estimates.html', estimates=Markup(html_table), css_style=css_style_markup)
                else:
                    return render_template('thankyou.html', css_style=css_style_markup)
        else:
            profile['profile_id'] = str(uuid.uuid4()) # Create new profile_id
            profile = add_to_profile(profile)

            # Select first design
            next_design = get_next_design(sample_thetas(theta_params, size_thetas), design_tuner)

            # Add next_design to design history and store placeholder for answer_history
            profile['design_history'] = [next_design]
            profile['answer_history'] = []

            # Put item into database
            table.put_item(Item=float_to_decimal(profile))
            profile['question_number'] = 'survey'
            output_design = convert_design(next_design, profile, profile)

            inputs = {'profile_id': profile['profile_id']}


            return render_template('survey.html', output_design=output_design, inputs=inputs, question_number=1, nquestions=nquestions, redirect_url='survey', css_style=css_style_markup)

# Utilities used by app.py
# Update JSONEncoder to handle dynamodb decimal type
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

# Format response to encode output as json
def format_response(data, code=200, content_type={'Content-Type': 'application/json'}):
    return json.dumps(data, cls=DecimalEncoder), code, content_type

# Get parameters from web request
def get_request(request):

    content_type = request.headers.get('Content-Type')
    if request.method=='GET':
        output = request.args
    else:
        if (content_type == 'application/json'):
            output = request.get_json()
        else:
            output = request.form.to_dict()

    return output
