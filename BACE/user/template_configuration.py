# Import statements
import numpy as np
import pandas as pd
import scipy.stats

# Import for taking cross product.
from itertools import product

##################################################
#######        General Parameters        #########
##################################################

# Input your name here.
author_name = 'Marshall Drake'

# Number of points sampled to form thetas. Tune `nsamples` for precision / speed.
nsamples = 1000

# Specify possible answers that can be observed. Binary choice experiment => [0, 1]
# Currently, all elements in answers must be integers.
answers = [0, 1]

##################################################
#######             Step 1:              #########
#######         Specify Designs          #########
##################################################

# Define a function, generate_designs_dataframe(), that returns a pandas.DataFrame representing designs that could be shown to respondents.
# Each column should represent a different design component and require no (nondefault) inputs.
def generate_designs_dataframe():
    """
    Function used to generate a pd.DataFrame containing all designs that can be shown to respondents.
    Ensure this function is deterministic and produces identical output each call to ensure compatibility across server instances.
    """
    # Create pd.DataFrame with column names
    designs = pd.DataFrame({
        "diff_price": np.linspace(start=-2, stop=2, num=41)
    })

    return designs

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
    { 
        "name": "wtp_attribute", 
        "distribution_type": "continuous", 
        "distribution": scipy.stats.norm(loc=1, scale=1) #N(1, 1)
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

    utility_difference = thetas['wtp_attribute']  - design['diff_price']    
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