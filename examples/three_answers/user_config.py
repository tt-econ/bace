# Example configuration file
import scipy.stats
import numpy as np

author = 'Your name here.' # Your name here
size_thetas = 5000 # Size of sample drawn from prior distribuion over preference parameters
answers = ['a', 'b', 'c'] # All possible answers that can be observed
max_opt_time = 10

# Add a constraint that x1 < x2
def constraint(samples):
    x1 = np.array([s['x1'] for s in samples])
    x2 = np.array([s['x2'] for s in samples])
    return x1 < x2

# Configuration Dictionary for Bayesian Optimization: See https://github.com/ARM-software/mango#6-optional-configurations for details
conf_dict = dict(
    domain_size=2000,
    # initial_random=1,
    # num_iteration=10,
    constraint=constraint
)

# Each element must be a scipy.stats object with an rvs method
theta_params = dict(
    x = scipy.stats.uniform(0, 1000),
    p = scipy.stats.uniform(.75, .24)
)

# Specify designs according to: https://github.com/ARM-software/mango#DomainSpace
design_params = dict(
    x1=scipy.stats.uniform(0, 1000),
    x2=scipy.stats.uniform(0, 1000)
)

# Specify likelihood function
def likelihood_pdf(answer, thetas, x1, x2):

    # Prefer 'a' if x < x1. 'b' if x1 <= x < x2. 'c' if x >= x2
    p = thetas['p']
    preferred_option = np.where(thetas['x'] <= x1, 'a', np.where(thetas['x'] <= x2, 'b', 'c'))

    # With probability 1-p you make a mistake and choose an alternative option randomly
    likelihood = np.where(preferred_option==answer, p, (1 - p)/2)

    return likelihood
