# Example configuration file
import scipy.stats
import numpy as np

author = 'Your name here.' # Your name here
size_thetas = 10000 # Size of sample drawn from prior distribuion over preference parameters
answers = [0, 1] # All possible answers that can be observed
max_opt_time = 5


# Configuration Dictionary for Bayesian Optimization
# See https://github.com/ARM-software/mango#6-optional-configurations for details
# Possible to add constraints and early stopping rules here.
conf_dict = dict(
    domain_size=2500,
    initial_random=2,
    num_iteration=10
)

# Preference parameters (theta_params)
# Dictionary where each preference parameter has a prior distribution specified by a scipy.stats distribution
# All entries must have a .rvs() and .log_pdf() method
theta_params = dict(
    amenity1=scipy.stats.uniform(loc=-10, scale=10),
    amenity2=scipy.stats.norm(loc=0, scale=3),
    p=scipy.stats.uniform(0.7, 0.29)
)

# Design parameters (design_params)
# Dictionary where each parameter specifies what designs can be chosen for a characteristic
# See https://github.com/ARM-software/mango#DomainSpace for details on specifying designs
design_params = dict(
    diff_wage=scipy.stats.uniform(0, 10), # Continuous
    diff_amenity1=[-1, 0, 1], # Range
    diff_amenity2=[-1, 0, 1] # Discrete
)

# Specify likelihood function
# Returns Prob(answer | theta, design) for each answer in answers
def likelihood_pdf(answer, thetas,
                   # All keys in design_params here
                   diff_wage, diff_amenity1, diff_amenity2):
    
   
    # Handle errors that come from overflow and division by zero
    with np.errstate(divide='ignore', over='ignore'):
        
        # Utility is linear in profile characteristics
        utility_diff = diff_wage + thetas['amenity1'] * diff_amenity1 + thetas['amenity2'] * diff_amenity2

    # Choose higher utility option with probability p. Randomly otherwise.
    u = utility_diff>0
    u[utility_diff==0] = 1/2
    likelihood = u * thetas['p'] + (1/2) * (1-thetas['p'])

    if str(answer)=='1':
        return likelihood
    else:
        return 1-likelihood


# # User configuration file
# theta_params = dict(
#     x=scipy.stats.uniform(loc=-10, scale=20)
# )

# # Design parameters (design_params)
# # Dictionary where each parameter specifies what designs can be chosen for a characteristic
# # See https://github.com/ARM-software/mango#DomainSpace for details on specifying designs
# design_params = dict(
#     diff_x=scipy.stats.uniform(-10, 20), # Continuous
# )

# # Specify likelihood function
# # Returns Prob(answer | theta, design) for each answer in answers
# def likelihood_pdf(answer, thetas,
#                    # All keys in design_params here
#                    diff_x):
    

#     p = 0.98
#     # Handle errors that come from overflow and division by zero
#     with np.errstate(divide='ignore', over='ignore'):
        
#         # Utility is linear in profile characteristics
#         utility_diff = thetas['x'] - diff_x

#     # Choose higher utility option with probability p. Randomly otherwise.
#     u = utility_diff>0
#     u[utility_diff==0] = 1/2
#     likelihood = u * p + (1/2) * (1-p)

#     if str(answer) == '1':
#         return likelihood
#     else:
#         return 1 - likelihood