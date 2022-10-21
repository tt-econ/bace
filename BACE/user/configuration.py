# # Import statements
import numpy as np
import pandas as pd
import scipy.stats

# Import for taking cross product.
from itertools import product

##################################################
#######        General Parameters        #########
##################################################

# Input your name here.
author_name = 'Your name here.'

# Number of points sampled to form thetas. Tune `nsamples` for precision / speed.
nsamples = 1000

# Specify possible answers that can be observed. Binary choice experiment => [0, 1]
# Currently, all elements in answers must be integers.
answers = [0, 1]

##################################################
#######             Step 1:              #########
#######         Specify Designs          #########
##################################################

# Specify either designs or bounds:
#     - designs (numpy ndarray). This should be specified if the researcher has a set range of questions that they want to use.
#         - A numpy ndarray object where each row is a potential design that can be shown to respondents. Only elements in designs will be shown to respondents.
#         - If designs is not None, then bounds is set to be the minimum and maximum value for each parameter based on the designs object. Ensures that optimization is performed over the grid.
#    - design_bounds (numpy ndarray). This specifies bounds for each parameter that can be asked. Element i in this array is a list with the minimum and maximum value for parameter i.
#         - This specifies a continuous design space that can be searched over
#
# The option that is not used should be set equal to None. For example, if you are using a continuous design space and set `design_bounds`, then set `designs=None`.

def generate_designs():

    design_values = [
        np.linspace(0, 5, num=51),
        np.array([1, 0, -1]),
        np.array([1, 0, -1])
    ]

    designs = np.array(list(product(*design_values)))

    return(designs)

designs = generate_designs() # Set to None if using a continuous design space.
design_bounds=None # Set to None if specifying a pre-determined designs grid.


##################################################
#######             Step 2:              #########
#######         Specify Thetas           #########
##################################################

# Each element in theta_parameters is a dictionary object that specifies the name and prior distribution for each possible parameter.
# This object is used to sample from the prior distribution and compute importance weights when updating posterior beliefs using Population Monte Carlo.
#
# Each element in theta_parameters is a dict object. Specify:
#   'name': Name of parameter
#   'distribution_type': 'continuous'
#   'distribution': Function that specifies the prior distribution. Any `scipy.stats` object satisfies the requirements. The function should have the following methods:
#       .rvs(size): Draw size random samples from the prior distribution.
#       .pdf(x): Calculates pdf of x given prior distribution.
#       .logpdf(x): Calculates logpdf of x given prior distribution.

theta_parameters = [
    { "name": "color", "distribution_type": "continuous", "distribution": scipy.stats.uniform(loc=-2, scale=4)}, # U(-2, 2)
    { "name": "pen_type", "distribution_type": "continuous", "distribution": scipy.stats.norm(loc=1, scale=1) }, # N(1, 1)
    { "name": "mu", "distribution_type": "continuous", "distribution": scipy.stats.uniform(loc=1, scale=9)}, # U(1, 10)
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
        `design`: Single `design`; this corresponds to a single row from `designs`. Each design parameter has a separate column and should be accessed by column index.
    Returns:
        likelihood (float): Likelihood of observing `answer`.

    # Notes: Take care to guarantee likelihood ε [0, 1] for all values of answers/thetas/designs.
    """

    with np.errstate(divide='ignore', over='ignore'):

        # Calculate utility difference
        utility_difference = -1 * design[0] + design[1] * thetas['color'] + design[2] * thetas['pen_type']
        likelihood = 1 / (1 + np.exp(-1 * thetas['mu'] * utility_difference))

    if (answer == 1):
        return likelihood
    else:
        return 1 - likelihood

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
