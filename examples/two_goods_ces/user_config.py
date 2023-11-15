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
    r=scipy.stats.norm(1, 5),
)

# Design parameters (design_params)
# Dictionary where each parameter specifies what designs can be chosen for a characteristic
# See https://github.com/ARM-software/mango#DomainSpace for details on specifying designs
design_params = dict(
    x1=scipy.stats.uniform(0, 100), # Continuous
    y1=scipy.stats.uniform(0, 100), # Continuous
    x2=scipy.stats.uniform(0, 100), # Continuous
    y2=scipy.stats.uniform(0, 100), # Continuous
)

# def ces(x, y, theta_x, theta_y, r):
#     return (theta_x * x ** r + theta_y * y ** r ) ** (1/r)
def ces(x, y, r):
    return (x ** r + y ** r ) ** (1/r)

# Specify likelihood function
# Returns Prob(answer | theta, design) for each answer in answers
def likelihood_pdf(answer, thetas,
                   # All keys in design_params here
                   x1, x2, y1, y2, ces=ces):
    r=1
    u1 = ces(x1, y1, thetas['r'])
    u2 = ces(x2, y2, thetas['r'])
    p = 1

    utility_diff = u2 - u1
    p = 0.98

    utility_diff = u2 - u1
   
    # Choose higher utility option with probability p. Randomly otherwise.
    u = utility_diff>0
    u[utility_diff==0] = 1/2
    likelihood = u*p + (1/2) * (1-p)

    if str(answer)=='1':
        return likelihood.astype(float)
    else:
        return (1-likelihood).astype(float)
