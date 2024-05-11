# Example configuration file
import scipy.stats
import numpy as np

author = 'Your name here.' # Your name here
size_thetas = 5000 # Size of sample drawn from prior distribuion over preference parameters
answers = [0, 1] # All possible answers that can be observed
max_opt_time = 5


# Configuration Dictionary for Bayesian Optimization
# See https://github.com/ARM-software/mango#6-optional-configurations for details
# Possible to add constraints and early stopping rules here.
conf_dict = dict(
    domain_size=2500,
    # initial_random=2,
    # num_iteration=10
)

# Preference parameters (theta_params)
# Dictionary where each preference parameter has a prior distribution specified by a scipy.stats distribution
# All entries must have a .rvs() and .log_pdf() method
theta_params = dict(
    r = scipy.stats.norm(1, 5),
    p = scipy.stats.uniform(.7, .29),
)

# Design parameters (design_params)
# Dictionary where each parameter specifies what designs can be chosen for a characteristic
# See https://github.com/ARM-software/mango#DomainSpace for details on specifying designs
design_params = dict(
    x1 = scipy.stats.uniform(0, 100), # Continuous
    y1 = scipy.stats.uniform(0, 100), # Continuous
    x2 = scipy.stats.uniform(0, 100), # Continuous
    y2 = scipy.stats.uniform(0, 100), # Continuous
)

# def ces(x, y, theta_x, theta_y, r):
#     return (theta_x * x ** r + theta_y * y ** r ) ** (1/r)
def ces(x, y, r):
    return (x ** r + y ** r ) ** (1/r)

# Specify likelihood function
# Returns Prob(answer | thetas, design) for each answer in answers
# Optionally allow for user's profile to be used as an input
def likelihood_pdf(answer, thetas, design, profile=None):
    u1 = ces(design['x1'], design['y1'], thetas['r'])
    u2 = ces(design['x2'], design['y2'], thetas['r'])

    base_utility_diff = u2 - u1

    # Choose higher utility option with probability p. Randomly otherwise.
    likelihood = (base_utility_diff > 0) * thetas['p'] + (1/2) * (1 - thetas['p'])

    eps = 1e-10
    likelihood[likelihood < eps] = eps
    likelihood[likelihood > (1 - eps)] = 1 - eps

    if str(answer)=='1':
        return likelihood
    else:
        return (1 - likelihood)
