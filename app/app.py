# Requirements
from flask_lambda import FlaskLambda
from flask import request, render_template, url_for, Markup
import uuid
import sys
import os
import json

# Individual imports
from database.db import table, update_db_item, float_to_decimal, decimal_to_float
from bace.bace_utils import format_response, get_request, sample_thetas
from bace.design_optimization import design_tuner, get_next_design
from bace.pmc_inference import pmc
from bace.user_config import theta_params, likelihood_pdf, author, size_thetas
from bace.user_convert import set_treatments, convert_design, nquestions

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

# Return a random design
@app.route('/random_design', methods=['GET'])
def random_design():
    design = design_tuner.ds.get_random_sample(size=1)[0]
    return format_response(design)

# Create a new profile in the database
@app.route('/create_profile', methods=['POST'])
def create_profile():

    # Store profile-specific information
    profile = get_request(request)
    profile['profile_id'] = str(uuid.uuid4()) # Create new profile_id
    profile = set_treatments(profile)

    # Select first design
    next_design = get_next_design(sample_thetas(theta_params, size_thetas), design_tuner)

    # Add next_design to design history and store placeholder for answer_history
    profile['design_history'] = [next_design]
    profile['answer_history'] = []

    # Put item into database
    table.put_item(Item=float_to_decimal(profile))
    next_design = convert_design(next_design, profile, profile)

    print(f'Successfully created profile for {profile.get("survey_id") or profile.get("profile_id")}')

    response = {
        'profile_id': profile.get('profile_id'),
        **next_design
    }

    return format_response(response)

# Update profile and return next design.
@app.route('/update_profile', methods=["POST"])
def update_profile():

    # Store profile specific information
    request_data = get_request(request)

    print(request_data)

    # If profile_id is present, proceed
    if request_data.get('profile_id') != "${e://Field/profile_id}":

        # Store profile key value and answer
        key={'profile_id': request_data.get('profile_id')}
        answer=request_data.get('answer')

        # Retrieve profile from database
        profile = table.get_item(Key=key)['Item']
        profile = decimal_to_float(profile)
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

        next_design = convert_design(next_design, profile, request_data)
        return format_response(next_design)
    
    else:
        # Select random design
        next_design = design_tuner.ds.get_random_sample(size=1)[0]
        profile = dict()
        next_design = convert_design(next_design, profile, request_data)
        return format_response(next_design)

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

            # Update item
            profile['answer_history'].append(answer)
            profile = decimal_to_float(profile)

            # Calculate estimates
            estimates = pmc(theta_params, profile['answer_history'], profile['design_history'], likelihood_pdf, size_thetas*10, J=10)
            estimates = estimates.agg(['mean', 'median']).to_dict()

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
        estimates = thetas.agg(['mean', 'median']).to_dict()
        # Return sample output
        return format_response(estimates)

@app.route('/survey', methods=["GET", "POST"])
def survey():

    if request.method == 'GET':
        return render_template('instructions.html', redirect_url='survey')
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
                next_design = convert_design(next_design, profile, profile)
                print(next_design)

                options = [
                    Markup(f'<label class="radio-container"><input type="radio" name="answer" value="0"><span class="radio-checkmark">{next_design["message_0_survey"]}</span></label>'),
                    Markup(f'<label class="radio-container"><input type="radio" name="answer" value="1"><span class="radio-checkmark">{next_design["message_1_survey"]}</span></label>')
                ]
                inputs = {'profile_id': profile['profile_id']}

                question = f'Question {len(profile.get("design_history"))} of {nquestions}: Which option do you prefer?'

                return render_template('survey.html', options=options, inputs=inputs, question=question, redirect_url='survey')
            
            else:

                estimates = thetas.agg(['mean', 'median'])

                # Store values to be updated
                updates = {
                    'answer_history': profile.get('answer_history'),
                    'estimates': estimates.to_dict()
                }

                # Push changes to database
                update_db_item(table, key, updates)

                # calculate the mean and median of the dataframe using agg()
                result_df = estimates.transpose()

                # add the parameter names as a separate column
                result_df['Parameter'] = result_df.index

                # reorder the columns then rename
                result_df = result_df[['Parameter', 'mean', 'median']]
                result_df.columns = ['Parameter', 'Mean', 'Median']

                # convert the dataframe into an html table
                html_table = result_df.to_html(index=False)

                return render_template('estimates.html', estimates=Markup(html_table))

        else:
            profile['profile_id'] = str(uuid.uuid4()) # Create new profile_id
            profile = set_treatments(profile)

            # Select first design
            next_design = get_next_design(sample_thetas(theta_params, size_thetas), design_tuner)

            # Add next_design to design history and store placeholder for answer_history
            profile['design_history'] = [next_design]
            profile['answer_history'] = []

            # Put item into database
            table.put_item(Item=float_to_decimal(profile))
            profile['question_number'] = 'survey'
            next_design = convert_design(next_design, profile, profile)

            options = [
                Markup(f'<label class="radio-container"><input type="radio" name="answer" value="0"><span class="radio-checkmark">{next_design["message_0_survey"]}</span></label>'),
                Markup(f'<label class="radio-container"><input type="radio" name="answer" value="1"><span class="radio-checkmark">{next_design["message_1_survey"]}</span></label>')
            ]
            inputs = {'profile_id': profile['profile_id']}

            question = f'Question {1} of {nquestions}: Which option do you prefer?'

            return render_template('survey.html', options=options, inputs=inputs, question=question, redirect_url='survey')