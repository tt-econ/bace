# Example configuration file
import scipy.stats
import numpy as np

author       = 'Pen Example Application' # Your name here
size_thetas  = 2500                      # Size of sample drawn from prior distribution over preference parameters.
max_opt_time = 5                         # Stop Bayesian Optimization process after max_opt_time seconds and return best design.

# example constraint: Remove designs where pen A is Blue and pen B is Black (i.e., ensuring color_a <= color_b)
# to be added to `conf_dict` below
# Other Mango constraint examples: https://github.com/ARM-software/mango/blob/main/examples/Constrained%20Optimization.ipynb
# def constraint(params):
#     color_a = np.array([s['color_a'] for s in params])
#     color_b = np.array([s['color_b'] for s in params])

#     return (color_a <= color_b)

# Configuration Dictionary for Bayesian Optimization
# See https://github.com/ARM-software/mango#6-optional-configurations for details
# early_stopping is additionally set in design_optimization.py
# constraint can be added as in the example above
conf_dict = dict(
    domain_size    = 1500,
    initial_random = 1,
    num_iteration  = 15,
    # constraint     = constraint
)

answers      = [0, 1]           # All possible answers that can be observed. Does not have to be binary.

# Preference parameters (theta_params)
# Dictionary where each preference parameter has a prior distribution specified by a scipy.stats distribution
# All entries must have a .rvs() and .log_pdf() method
# See https://docs.scipy.org/doc/scipy/reference/stats.html
theta_params = dict(
    blue_ink = scipy.stats.uniform(loc=-2, scale=4),
    gel_pen  = scipy.stats.norm(loc=1, scale=1),
    mu       = scipy.stats.uniform(loc=1, scale=9)
)

# Design parameters (design_params)
# Dictionary where each parameter specifies what designs can be chosen for a characteristic
# See https://github.com/ARM-software/mango#DomainSpace for details on specifying designs
design_params = dict(
    price_a   = scipy.stats.uniform(0.5, 5),
    price_b   = scipy.stats.uniform(0.5, 5),
    color_a   = ['Black', 'Blue'],
    color_b   = ['Black', 'Blue'],
    type_a    = ['Ballpoint', 'Gel'],
    type_b    = ['Ballpoint', 'Gel']
)

# Specify likelihood function
# Returns Prob(answer | thetas, design) for each answer in answers
# Optionally allow for user's profile to be used as an input
def likelihood_pdf(answer, thetas, design, profile=None):

    base_U_a = - design['price_a'] + thetas['blue_ink'] * (design['color_a'] == 'Blue') + thetas['gel_pen'] * (design['type_a'] == 'Gel')
    base_U_b = - design['price_b'] + thetas['blue_ink'] * (design['color_b'] == 'Blue') + thetas['gel_pen'] * (design['type_b'] == 'Gel')
    base_utility_diff = base_U_b - base_U_a

    # Logit likelihood of choosing B over A with scale parameter thetas['mu']
    likelihood = 1 / (1 + np.exp(-1 * thetas['mu'] * base_utility_diff))

    # Likelihood should be strictly between 0 and 1
    eps = 1e-10
    likelihood[likelihood < eps] = eps
    likelihood[likelihood > (1 - eps)] = 1 - eps

    # Produce a likelihood associated with each possible answer choice
    # (account for the fact that answer inputs through the API may be in string format)
    if str(answer) == '1':
        # choose B
        return likelihood
    else:
        # choose A
        return 1 - likelihood
