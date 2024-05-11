# Example configuration file
import scipy.stats
import numpy as np

author       = 'Pen Example Application' # Your name here
size_thetas  = 2500                      # Size of sample drawn from prior distribution over preference parameters.
max_opt_time = 5                         # Stop Bayesian Optimization process after max_opt_time and return best design.

# example constraint (only 1 characteristic differing at a time)
# to be added to `conf_dict` below
# Other Mango constraint examples: https://github.com/ARM-software/mango/blob/main/examples/Constrained%20Optimization.ipynb
# def constraint(params):
#     color_diff = np.array([s['color_diff'] for s in params])
#     type_diff = np.array([s['type_diff'] for s in params])

#     return (abs(color_diff) + abs(type_diff) <= 1)

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
design_params    = dict(
    price_diff   = scipy.stats.uniform(-5, 10),
    color_diff   = [-1, 0, 1],
    type_diff    = [-1, 0, 1],
)

# Specify likelihood function
# Returns Prob(answer | theta, design) for each answer in answers
def likelihood_pdf(answer, thetas, design):

    eps = 1e-10

    # Only utility difference matters
    # design['price_diff'] = price of pen B - price of pen A
    # design['color_diff'] = 1 if pen B is Blue and pen A is Black (and -1 if the opposite); thetas['blue_ink']: utility from having Blue over Black
    # design['type_diff'] = 1 if pen B is Gel and pen A is Ballpoint; thetas['gel_pen']: utility from having Gel over Ballpoint

    base_utility_diff = (
            - design['price_diff'] +
            thetas['blue_ink'] * design['color_diff'] +
            thetas['gel_pen'] * design['type_diff']
        )

    # Logit likelihood of choosing B over A with scale parameter thetas['mu']
    likelihood = 1 / (1 + np.exp(-1 * thetas['mu'] * base_utility_diff))

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
