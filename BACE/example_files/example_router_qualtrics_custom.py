from fastapi import APIRouter
import numpy as np
from functools import partial

# Custom Imports
from BACE.user.configuration import nsamples, likelihood_pdf, theta_parameters, answers, n_starting_points, n_iterations, designs, design_bounds, sample_designs, max_time
from BACE.utils import sample_parameters, rename_cols
from BACE.models import  DesignModel
from BACE.design_optimization import bayesian_optimization, expected_improvement
from BACE.filter_pmc import pmc_filter
from BACE.database_queries import create_and_insert_profile, get_profile, update_design_history, update_full_profile, update_final

from BACE.user.custom_models import CreateRequest, FirstDesignRequest, UpdateChooseRequest, UpdateReturnEstimatesRequest, ResponseModel
from BACE.user.design_details import characteristics, convert_design

from BACE.db import pool

router = APIRouter(
    prefix="/qualtrics_custom",
    tags=["qualtrics"]
)

# Create profile in database for new user.
@router.post('/create_profile', response_model=ResponseModel)
def create_profile(prof: CreateRequest):
    """
    Creates entry in database to store information for a specific profile id.
    If request parameter test = "test", then it returns an example response to help fill embedded data in Qualtrics.
    """

    if prof.test == 'test':
        
        # Set test profile id
        profile_id = 0   

    else:
        
        # Sample thetas to form prior distribution
        thetas = sample_parameters(theta_parameters, nsamples)

        # Create entry in database. Return profile id that will be used to access entry.
        profile_id = create_and_insert_profile(pool, prof.survey_id, thetas)
        profile_id = int(profile_id.profile_id)

    # Prepare response
    response = ResponseModel(response = {
        'profile_id': profile_id,
        'color_info': characteristics['color'],
        'type_info': characteristics['pen_type']
    })

    return response

@router.put('/first_design', response_model=ResponseModel)
def first_design(prof: FirstDesignRequest):
    """
    Compute and return first design
    Inputs:
        QualtricsRequest model form
    Returns:
        Converted design and required information for setting up Qualtrics questions.
    """

    if prof.test == "test":

        # Select first design
        next_design = sample_designs(1)[0]

    else:
        # Retrive profile entry from database
        this_profile = get_profile(pool, prof.profile_id)

        # Calculate optimal next design
        next_index, next_design = bayesian_optimization(
            this_profile.get('thetas'), 
            designs, 
            answers, 
            likelihood_pdf, 
            expected_improvement, 
            n_starting_points, 
            n_iterations,
            max_time
        )

        # Update design history in database
        this_profile['design_history'].append(next_design.tolist())
        update_design_history(pool, this_profile.get('profile_id'), this_profile.get('design_history'))

    # Convert output for embedded data
    base, treat, design = convert_design(next_design, characteristics, question_no=0)

    response = ResponseModel(response = {
        "base": base,
        "treat": treat,
        "design": design
    })

    return response

# Update posterior and choose next design.
@router.put('/update_and_choose', response_model=ResponseModel)
def update_and_choose(prof: UpdateChooseRequest):

    if prof.test == 'test':
        # Generate sample feedback for setting up embedded data in Qualtrics

        # Set sample values for next design, numeraire, and characteristics
        next_design = sample_designs(1)[0]

    else:

        # Retrieve profile data from database
        this_profile = get_profile(pool, prof.profile_id)

        # Update answer_history with chosen answer
        this_profile['answer_history'].append(prof.answer)

        # Update posterior using pmc algorithm and observed answer
        new_thetas = pmc_filter(
            thetas=this_profile['thetas'],
            design_history=this_profile['design_history'],
            answer_history=this_profile['answer_history'],
            likelihood_pdf=likelihood_pdf,
            theta_parameters=theta_parameters,
            N=nsamples
        )

        # Select optimal design using new posterior
        # Calculate optimal next design using updated posterior
        next_index, next_design = bayesian_optimization(
            thetas=new_thetas, 
            designs=designs, 
            answers=answers, 
            likelihood_pdf=likelihood_pdf, 
            acquisition_f=expected_improvement, 
            n_starting_points=n_starting_points, 
            n_iterations=n_iterations,
            max_time=max_time
        )
        # Update database entry with new design history and posterior
        this_profile['design_history'].append(next_design.tolist())
        this_profile['thetas'] = new_thetas
        update_full_profile(pool, this_profile)

    # Convert output for embedded data
    base, treat, design = convert_design(next_design, characteristics, prof.question_no)

    response = ResponseModel(response = {
        "base": base,
        "treat": treat,
        "design": design
    })

    return response

# Update posterior. Compute mean and mode posterior estimates.
@router.put('/update_and_return_estimates', response_model=ResponseModel)
def return_estimates(prof: UpdateReturnEstimatesRequest):

    if prof.test == 'test':
        # Generate sample feedback for setting up embedded data in Qualtrics

        # Sample randomly from prior distribution.        
        new_thetas = sample_parameters(theta_parameters, 100)

    else:
        # Retrieve profile from database
        this_profile = get_profile(pool, prof.profile_id)

        # Update answer_history with chosen answer
        this_profile['answer_history'].append(prof.answer)

        # Update posterior using pmc algorithm
        new_thetas = pmc_filter(
            thetas=this_profile['thetas'],
            design_history=this_profile['design_history'],
            answer_history=this_profile['answer_history'],
            likelihood_pdf=likelihood_pdf,
            theta_parameters=theta_parameters,
            N=nsamples
        )

        # Update profile to hold new posterior and answer_historr
        this_profile['thetas'] = new_thetas
        update_final(pool, this_profile)

    # Calculate mean/mode posterior estimates and convert output.
    mean_estimates = new_thetas.mean().to_frame().T
    mean_estimates = rename_cols('mean', mean_estimates)

    response = ResponseModel(response = mean_estimates)

    return response

# Return random design.
@router.get('/random_design', response_model=ResponseModel)
def random_design():
    """
    Select random design
    Output:
        BACE.models.DesignModel
    """
    # Select Random design

    design = sample_designs(1)[0]

    base, treat, design = convert_design(design, characteristics, "random")

    response = ResponseModel(response = {
        "base": base,
        "treat": treat,
        "design": design
    })

    return response