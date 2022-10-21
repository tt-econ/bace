from fastapi import APIRouter
from psycopg.rows import class_row
import numpy as np
import pandas as pd

# Custom Imports
from BACE.user.configuration import nsamples, likelihood_pdf, theta_parameters, answers, n_starting_points, n_iterations, designs, design_bounds, sample_designs, max_time
from BACE.utils import sample_parameters, rename_cols
from BACE.models import  DesignModel, ProfileIn, CreateProfile, UpdateProfile
from BACE.design_optimization import bayesian_optimization, expected_improvement
from BACE.filter_pmc import pmc_filter
from BACE.database_queries import create_and_insert_profile, get_profile, update_design_history, update_full_profile, update_final

from BACE.db import pool

router = APIRouter(
    prefix="/standard",
    tags=["standard"]
)

# Create profile in database for new user.
@router.post('/create_profile', response_model=ProfileIn)
def create_profile(prof: CreateProfile):
    """
    Create profile entry in database for individual. Store prior distribution and return unique profile_id that will be used to access entry.
    Input:
        prof: CreateProfile model (BACE.models.CreateProfile)
    Output:
        BACE.models.ProfileIn
    """

    # Sample from prior distribution
    thetas = sample_parameters(theta_parameters, nsamples)

    # Create profile entry and store prior distribution. Return unique profile_id.
    profile_id = create_and_insert_profile(pool, prof.survey_id, thetas)

    return ProfileIn(profile_id=profile_id.profile_id)

@router.put('/first_design', response_model=DesignModel)
def first_design(prof: ProfileIn):
    """
    Compute and return first design.

    Inputs:
        BACE.models.ProfileIn
            Contains profile_id (int) of individual.
    Returns:
        BACE.models.DesignModel
            Converted design and required information for setting up Qualtrics questions.
    
    Takes in profile_id (int) as input. Retrieves profile from database.
    Computes the optimal next question using the Bayesian optimization algorithm.
    Updates design_history in database. Returns chosen design.
    """

    # Retrive profile entry from database
    this_profile = get_profile(pool, prof.profile_id)

    # Choose optimal next design.
    next_index, next_design = bayesian_optimization(
        thetas=this_profile.get('thetas'), 
        designs=designs, 
        answers=answers, 
        likelihood_pdf=likelihood_pdf, 
        acquisition_f=expected_improvement, 
        n_starting_points=n_starting_points, 
        n_iterations=n_iterations,
        max_time=max_time
        )

    # Update design history in database
    this_profile['design_history'].append(next_design.tolist())
    update_design_history(pool, this_profile.get('profile_id'), this_profile.get('design_history'))

    # Return next design
    return(DesignModel(design=next_design.tolist()))

# Update posterior and choose next design.
@router.put('/update_and_choose', response_model=DesignModel)
def update_and_choose(prof: UpdateProfile):
    """
    Update posterior after observing answer. Calculate next optimal design and return.
    Input:
        BACE.models.UpdateProfile
    Output:
        BACE.models.DesignModel
    """

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

    print(this_profile)
    update_full_profile(pool, this_profile)

    # Return optimal design
    return(DesignModel(design=next_design.tolist()))

# Update posterior. Compute mean and mode posterior estimates.
@router.put('/update_and_return_estimates')
def return_estimates(prof: UpdateProfile):
    """
    Update posterior. Return mean and mode posterior estimates.
    Input:
        BACE.models.UpdateProfile
    Output:
        Dictionary with mean and mode (nearest int) estimates for each parameter.
    """

    # Retrive profile
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

    # Update profile with new answer_history and posterior thetas
    this_profile['thetas'] = new_thetas
    update_final(pool, this_profile)

    # Calculate mean and mode posterior estimates. Format for return
    mean_estimates = new_thetas.mean().to_frame().T
    mean_estimates = rename_cols('mean', mean_estimates)

    estimates = {}
    estimates.update(mean_estimates)

    return(estimates)

# Return random design.
@router.get('/random_design', response_model=DesignModel)
def random_design():
    """
    Select random design
    Output:
        BACE.models.DesignModel
    """
    # Select Random design

    design = sample_designs(1)[0]

    return DesignModel(design=design.tolist())