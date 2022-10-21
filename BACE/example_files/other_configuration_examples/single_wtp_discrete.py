import numpy as np
import pandas as pd
import scipy.stats

# Import for taking cross product.
from itertools import product

##################################################
#######        General Parameters        #########
##################################################

# Input your name here.
author_name = 'Discrete Example - Single product attribute WTP.'
nsamples = 5000
answers = [0, 1]

##################################################
#######             Step 1:              #########
#######         Specify Designs          #########
##################################################

designs=np.linspace(start=-5, stop=5, num=41) # (-5, -4.75, -4.5, ..., 4.5, 4.75, 5)
design_bounds=None

##################################################
#######             Step 2:              #########
#######         Specify Thetas           #########
##################################################

# Estimate WTP for the attribute. Prior is that users value the attribut between -3 and 3 dollars.
# Estimate consistency. Choose randomly with probability 1- thetas['p']
theta_parameters = [
    { 
        "name": "wtp_attribute", 
        "distribution_type": "continuous", 
        "distribution": scipy.stats.uniform(loc=-3, scale=6) #U(-3, 3)
        }, 
    { 
        "name": "p", 
        "distribution_type": "continuous", 
        "distribution": scipy.stats.uniform(loc=1/2, scale=1/2) # U(1/2, 1)
        }, 
]

##################################################
#######             Step 3:              #########
#######      Specify likelihood_pdf      #########
##################################################

def likelihood_pdf(answer, thetas, design):
    """
    Returns P(answer | thetas, design)
    For an individual with preference parameters `thetas`, this function outputs the likelihood of observing every possible `answer` for any `design` in `designs`.

    Input:
        `answer`: Must be an element in `answers`.
        `thetas`: DataFrame of preference parameters. This will correspond to the DataFrame generated from `theta_parameters` above. Each parameter has a separate column and can be accessed by name. For example, to access parameter `x`, you can select `thetas['x']`.
        `design`: Single `design`; this corresponds to a single row from `designs`. Each design parameter has a separate column and can be accessed by name. For example, to access the `alpha` design parameter, you can type `design['alpha']`.
    Returns:
        likelihood (float): Likelihood of observing `answer`.

    # Notes: Take care to guarantee likelihood ε [0, 1] for all values of answers/thetas/designs.
    """

    utility_difference = thetas['wtp_attribute']  - design[0]    
    likelihood_attribute_option = (utility_difference > 0) * thetas['p'] + (1/2) * ( 1 - thetas['p'] )

    if (answer == 1):
        return likelihood_attribute_option
    else:
        return 1 - likelihood_attribute_option

##################################################
#######        Tuning Parameters         #########
##################################################

# Bayesian Optimization parameters
n_starting_points = 10 # Number of randomly selected initial points.
n_iterations = 15 # Number of rounds of model fitting.
max_time=10






#########################################################################
###############                                      ####################
###############            Do not change             ####################
###############                                      ####################
#########################################################################

def get_design_components(designs=None, design_bounds=None):

    if designs is None and design_bounds is None:
        raise "Specify designs or bounds objects in BACE/user/configuration.py"

    if designs is not None:

        if len(designs.shape) == 1:
            designs = designs.reshape(len(designs), 1)

        def sample_designs(N=1, designs=designs, design_bounds=design_bounds, replace=False):

            if N >= len(designs):
                replace=True

            sampled_indices = np.random.choice(a=len(designs), size=N, replace=replace)
            
            return designs[sampled_indices]

        design_bounds = np.transpose(np.array([
            np.min(designs, axis=0),
            np.max(designs, axis=0)
        ]))

    else:

        def sample_designs(N=1, designs=designs, design_bounds=design_bounds, replace=False):

            return np.random.uniform(low = design_bounds[:, 0], high=design_bounds[:, 1], size=(N, len(design_bounds)))

    return designs, design_bounds, sample_designs

designs, design_bounds, sample_designs = get_design_components(designs, design_bounds)
