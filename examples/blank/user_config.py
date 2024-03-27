# Example configuration file
import scipy.stats
import numpy as np

author = 'Your name here.' # Your name here
size_thetas = 2500 # Size of sample drawn from prior distribuion over preference parameters.
max_opt_time = 5 # Stop Bayesian Optimization process after max_opt_time and return best design.

# Configuration Dictionary for Bayesian Optimization
# See https://github.com/ARM-software/mango#6-optional-configurations for details
# early_stopping is additionally set in design_optimization.py
# constraint can also be added
conf_dict = dict(
    # domain_size=1500,
    # initial_random=1,
    # num_iteration=15
)

answers      = [0, 1]           # All possible answers that can be observed. Does not have to be binary.

# Preference parameters (theta_params)
# Dictionary where each preference parameter has a prior distribution specified by a scipy.stats distribution
# All entries must have a .rvs() and .log_pdf() method
# See https://docs.scipy.org/doc/scipy/reference/stats.html
theta_params = dict(
    # param_a = scipy.stats.norm()
)

# Design parameters (design_params)
# Dictionary where each parameter specifies what designs can be chosen for a characteristic
# See https://github.com/ARM-software/mango#DomainSpace for details on specifying designs
design_params = dict(
    # continuous_param = scipy.stats.uniform(0, 10),
    # categorical_param = [1, 2, 3]
)

# Specify likelihood function
# Returns Prob(answer | theta, design) for each answer in answers (can be in string format from API)
def likelihood_pdf(answer, thetas,
                   # All keys in design_params here
                   # design_continuous, design_discrete
                   ):

    if answer == '1':
        return 1
    else:
        return 0
