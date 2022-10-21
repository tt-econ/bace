import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from scipy.optimize import minimize

from BACE.user.configuration import designs, design_bounds, sample_designs

import time

def mutual_information(thetas, answers, likelihood_pdf, design):
    """
    Formula for calculating the mutual information. The utility function we are maximizing when optimizing future designs.

    Input:
        thetas: (n x d DataFrame) contains population of theta parameters
        answers: possible answers that likelihood can take on
        likelihood_pdf: returns l(answer | theta, design)
        design: design we are evaluating mutual information at
    
    Returns:
        mutual_info: Mutual information given design
    """

    # Note for computation, we only need to calculate the likelihood and normalizing constants for n-1 answers since probabilities sum to 1
    # likelihood(final_option) = 1 - sum(likelihood(other options))
    # mean(likelihood(final_option)) = 1 - sum(mean(likelihood(other_options)))

    # Initialize components for final option
    likelihood_final_option = np.ones(len(thetas))
    mean_final_option = 1

    # Initialize mutual_info to keep track of sum.
    mutual_info = 0

    # Calculate components for all but final answer option.
    for answer in answers[:-1]:

        # Compute likelihood of observing answer to design given preferences theta 
        likelihood = likelihood_pdf(answer, thetas, design)

        # Compute mean
        mean_likelihood = np.mean(likelihood)

        # Compute mutual information for given answer
        with np.errstate(divide='ignore'):
            mutual_info_component = np.mean(likelihood * np.log(likelihood)) - mean_likelihood * np.log(mean_likelihood)

        mutual_info += mutual_info_component

        # Update components for final option
        likelihood_final_option -= likelihood
        mean_final_option -= mean_likelihood

    # For numerical reasons, set zeroes equal to eps
    likelihood_final_option[likelihood_final_option == 0] = np.finfo(float).eps
    mean_final_option = np.finfo(float).eps if mean_final_option==0 else mean_final_option

    # Add information from final option
    with np.errstate(divide='ignore'):
        mutual_info_final_component = np.mean(likelihood_final_option * np.log(likelihood_final_option)) - mean_final_option * np.log(mean_final_option)
        
    mutual_info += mutual_info_final_component

    # Return total mutual information. Return 0 if mutual_info < 0 due to numerical issues. 
    return mutual_info if mutual_info > 0 else 0


def grid_search(thetas, designs, answers, likelihood_pdf, sample_percentage=100):
    """
    Compute the mutual information for sample_percentage % of randomly selected designs.
    Return design with highest mutual_information.

    Input:
        thetas: numpy array containing population of hypothesized parameters in grid
        designs: dict containing the full set of designs that can be asked.
        answers: arr containing all possible answers to designs
        likelihood_pdf: function that evaluates the l(answer | theta, design)
        sample_percentage (default=100): the percentage of randomly selected designs at which to calculate the mutual information

    Returns:
        best_design_index (int): key for design with highest mutual information
        best_design (arr): value for designs[best_design_key]

    """

    # Require sample_percentage to be in [1, 100].
    assert (1 <= sample_percentage  <= 100), "sample_percentage must be in [1, 100]."

    if sample_percentage < 100:
        # Number of designs to sample
        n_designs = round(sample_percentage/100 * len(designs))
        designs_sample = designs.sample(n_designs)
    else:
        designs_sample = designs
    
    # Calculate mutual information for selected designs
    mutual_info = {d_index: mutual_information(thetas, answers, likelihood_pdf, designs.loc[d_index]) for d_index in designs_sample.index}

    # Find index for design with highest mutual information.
    best_design_index = max(mutual_info, key=mutual_info.get)

    # Return index and best design
    return best_design_index, designs.loc[best_design_index, :]


def expected_improvement(data, designs, model, xi=0.):
    """
    Computes and returns expected improvement obtained from evaluating the target function at all points in designs.

    EI(x) = E[max(f(x) - f(x*), 0)] where x* = argmax(f(xi)) for xi in data

    Input:
        data: designs that model has previously been evaluated at
        designs: DataFrame of all designs
        model: Gaussian Process Regressor
        xi: Parameter to tune exploration/exploitation tradeoff. Higher 
    """

    # Calcualte highest predicted value based on current data
    yhat = model.predict(data)
    sample_best = np.max(yhat)

    # Predict y for all designs in d
    mu, std = model.predict(
        designs,
        return_std=True
    )

    # Calculate expected improvement for all possible designs in `designs`
    with np.errstate(divide='warn'):

        improvement = mu - sample_best - xi
        Z = improvement / std

        e_improvement = improvement * norm.cdf(Z) + std * norm.pdf(Z)

        # Drop values with zero sd (Explore new designs)
        e_improvement[std==0.0] = 0.0
    
    return e_improvement


def bayesian_optimization(thetas, designs, answers, likelihood_pdf, acquisition_f=expected_improvement, n_starting_points=10, n_iterations=15, max_time=10, xi=0.):
    """
    Find the design with the highest mutual information using Bayesian Optimization to select designs.
    Returns design with highest mutual_information.

    Input:
        thetas: DataFrame containing population of hypothesized parameters in grid
        designs: DataFrame containing the full set of designs that can be asked.
        answers: arr containing all possible answers to designs
        likelihood_pdf: function that evaluates the l(answer | theta, design)
        acquisition_f: acquisition function to evaluate proposed future locations
        n_starting_points (int): Number of randomly chosen designs to start search
        n_iterations (int): Number of iterations of Bayesian Optimization algorithm.
        xi: parameter governing exploitation/exploration tradeoff

    Returns:
        best_design_key (int): key for design with highest mutual information
        best_design (arr): value for designs[best_design_key]
    """

    start_time = time.time()

    # Initialize Gaussian Process Regressor
    model = GaussianProcessRegressor()

    # Calculate mutual information at n_starting_points randomly chosen designs.
    sampled_designs = sample_designs(N=n_starting_points)
    y = [mutual_information(thetas, answers, likelihood_pdf, design) for design in sampled_designs]

    best_y = np.max(y)
    best_index = np.argmax(y)

    # Update model for n_iterations by selecting the next design with the highest improvement in mutual_information using Bayesian Optimization
    for i in range(n_iterations):

        # Fit model using data from initial sample
        model.fit(sampled_designs, y)

        # Propose location of next best point
        proposed_design = propose_location(acquisition_f, sampled_designs, designs, model, xi)

        # Compute mutual_information at proposed value
        proposed_y = mutual_information(thetas, answers, likelihood_pdf, proposed_design)

        # Record new data
        #sampled_designs = sampled_designs.append(proposed_design, ignore_index=False)
        sampled_designs = np.concatenate((sampled_designs, [proposed_design]), axis=0)
        y = np.append(y, proposed_y)

        # Update best index
        if proposed_y > best_y:
            best_y = proposed_y
            best_index = np.argmax(y)

        if time.time() - start_time >= max_time:
            print("Bayesian Optimization exited early due to time limit.")
            break

    # Find design with highest mutual_information
    best_design = sampled_designs[best_index]

    return best_index, best_design

def propose_location(acquisition_f, data, designs, model, xi=0.):
    """
    Proposes next design to evaluate mutual information at based on GPR model and chosen acquisition function.
    Returns proposed design for next mutual_information evaluation

    Input:
        thetas: DataFrame containing population of hypothesized parameters in grid
        data: DataFrame. Contains mutual information for previously evaluated sample of designs.
        designs: DataFrame containing the full set of designs that can be asked.
        model: Gaussian Process Regressor.
        xi: parameter governing exploitation/exploration tradeoff

    Returns:
        best_design_key (int): key for design with highest mutual information
        best_design (arr): value for designs[best_design_key]
    """

    # Calculate improvement scores according to acquisition_f
    t0= time.time()

    nrestarts = 1
    min_val = 1
    min_x = None

    def min_obj(X):
        return -acquisition_f(data, X.reshape(1, -1), model, xi)

    x0s = sample_designs(nrestarts)

    for x0 in x0s:
        
        res = minimize(min_obj, x0=x0, bounds=design_bounds, method="L-BFGS-B")
        if res.fun < min_val:
            min_val = res.fun
            min_x = res.x

    if designs is not None:
        proposed_design = find_closest_design(min_x.reshape(1, -1), designs)
    else:
        proposed_design = min_x
   
    return proposed_design

def find_closest_design(design, designs):
    """
    Find closest element in designs to design using Euclidean distance.
    """
    closest_index = np.argmin(np.sum(np.square(np.subtract(designs, design)), axis=1))

    return designs[closest_index, :]
