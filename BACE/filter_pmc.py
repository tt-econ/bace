# PMC Basic Algorithm in Python
import numpy as np
import pandas as pd
import scipy.stats

def pmc_filter(thetas, design_history, answer_history, likelihood_pdf, theta_parameters, N, J=5, scale_factors=np.array([1/10, 1/2, 1, 2, 10])):
    """
    Uses population monte carlo algorithm (Cappe 2004) to update location of proposed thetas using resampling based on importance weights.

    Input:
        thetas (Data.Frame): current population of thetas
        design_history (list): History of previous designs that have been asked.
        answer_history (list): History of previous answers that hae been asked
        likelihood_pdf (function): target distribution we want to model. Typically, l(answer | theta, design) * prior(theta)
        theta_parameters (dict): Object specifying prior distribution for each parameter. Defined in BACE/user/configuration.py
        N (int): number of thetas to propogate forward by resampling with replacement
        J (int): Number of iterations of pmc algorithm
        scale_factors (arr): Array of values used to scale importance sampling distribution.

    Returns:
        thetas (DataFrame): DataFrame containing `N` draws from posterior distribution.

    """
    
    if N is None:
        N = len(thetas)

    # scale_eps is used to carry forward scale_factors with positive probability
    scale_eps = np.round(N/100)
    nscale = len(scale_factors)

    # Compute current standard deviation
    current_sd = thetas.std()

    for j in range(J):

        # Specify thetas_start and scale_weights if first iteration
        if j == 0:
            start_thetas = thetas.copy()
            scale_weights = np.full(nscale, fill_value=1/nscale)
        
        # Scample N indices from scale_factors. Store logpmf.
        scale_indices = np.random.choice(nscale, size=N, replace=True, p=scale_weights)
        #scale_logpmf = np.log(scale_weights[scale_indices])

        # Scale sd by randomly selected scale_indices
        scale = np.outer(scale_factors[scale_indices], current_sd)

        # Importance sample around existing points.
        new_thetas = pd.DataFrame(
            data = scipy.stats.norm.rvs(size=start_thetas.shape, loc=start_thetas, scale=scale),
            columns = list(start_thetas.columns)
        )

        # Compute loglikelihood of sampling new_thetas | start_thetas. Sum by row.
        # q_logpdf = scipy.stats.norm.logpdf(new_thetas, loc=start_thetas, scale=scale)
        # q_logpdf = np.sum(q_logpdf, axis=1)
        q_logpdf = compute_q_logpdf(new_thetas, start_thetas, current_sd, scale_factors, scale_weights)

        # Compute loglikelihood of observing new_thetas | prior
        prior_logpdf = compute_prior_logpdf(new_thetas, theta_parameters)

        # Compute loglikelihood of p(answer_history | new_thetas, design_history)
        lklhd_logpdf = compute_lklhd_logpdf(new_thetas, answer_history, design_history, likelihood_pdf)

        # Compute weights. Use of M is better for numerical stability. Subtract scale_logpmf to control for likelihood of sampling different scale factors.
        log_w = lklhd_logpdf + prior_logpdf - q_logpdf
        M = np.max(log_w)
        w = np.exp(log_w - M)
        w[np.isnan(w)] = 0

        # Normalize w
        w = w / np.sum(w)

        # Store thetas and w
        if j == 0:
            theta_history = new_thetas.copy()
            w_history = w
        else:
            theta_history = pd.concat([theta_history, new_thetas], ignore_index=True)
            w_history = pd.concat([w_history, w], ignore_index=True)
        
        # Resample start_thetas with replacement using w.
        new_indices = systematic_sample(w, N)
        start_thetas = new_thetas.iloc[new_indices, :].reset_index(drop=True)

        # Update scale_weights
        scale_weights = []

        for x in scale_factors:
            scale_weight = scale_eps + np.sum(scale_factors[scale_indices[new_indices]]==x)
            scale_weights.append(scale_weight)

        scale_weights = scale_weights / np.sum(scale_weights) # Normalize scale_weights

    # After final round normalize w_history
    w_history = w_history / np.sum(w_history)
    
    # Resample N particles from theta_history using weights w_history and return.
    final_indices = systematic_sample(w_history, N)
    final_thetas = theta_history.iloc[final_indices, :].reset_index(drop=True)

    return final_thetas

def compute_q_logpdf(new_thetas, start_thetas, current_sd, scale_factors, scale_weights):
    """
    Compute the denominator. Weighted sum of 
    """

    # Initialize variables.
    pdf = 0
    K = len(scale_factors)

    for k in range(K):

        # Compute scale
        scale_k = scale_factors[k] * current_sd

        # Compute pdf_k
        try:
            pdf_k = scale_weights[k] * np.exp(np.sum(scipy.stats.norm.logpdf(new_thetas, loc=start_thetas, scale=scale_k), axis=1))
            pdf += pdf_k
        except:
            print(new_thetas)
            print(start_thetas)
            print(scale_k)

            raise ValueError
    
    # Return logpdf
    return np.log(pdf)

def compute_prior_logpdf(thetas, theta_parameters):
    """
    Computes logpdf of observing values in thetas given the prior distributions defined in BACE/user/configuration.
    Inputs:
        thetas: pandas.DataFrame containing sample of thetas.
        theta_parameters: Object that defines prior distribution for each column in thetas.
    Returns:
        prior_logpdf: logpdf of observing each row in thetas.
    """
    # Initialize output array
    prior_logpdf = np.zeros(len(thetas))

    for param in theta_parameters:
        # Compute logpdf of thetas given prior
        param_logpdf = param["distribution"].logpdf(thetas[param["name"]])
        prior_logpdf += param_logpdf

    return prior_logpdf

def compute_lklhd_logpdf(thetas, answer_history, design_history, likelihood_pdf):
    """
    Computes the logpdf of the observed answer history given the population of thetas and design_history.
    Inputs:
        thetas: DataFrame containing sample of thetas.
        answer_history: Array of answers to previously asked designs.
        design_history: DataFrame of designs that have been asked
        likelihood_pdf: Function that computes pdf of observing answer given thetas and a given design.
    Returns:
        lklhd_logpdf: log(P(answer_history | thetas, design_history))
    """
    assert len(answer_history) == len(design_history), "Error: answer_history and design_history are of different lengths."
    ND = len(design_history)

    # Initialize lklhd_logpdf
    lklhd_logpdf = 0

    for i in range(ND):
        # Compute p(answer_i | thetas, design_i)
        lklhd = likelihood_pdf(int(answer_history[i]), thetas, design_history[i])

        with np.errstate(divide='ignore', invalid='ignore'):
            log_lklhd = np.log(lklhd)
            log_lklhd[np.isnan(log_lklhd)] = -np.inf

        lklhd_logpdf += log_lklhd
    
    return lklhd_logpdf

def systematic_sample(weights, N=None):
    """
    Systematic sample N indices from an array of weights.
    Inputs:
        weights: array of weights. Must be weakly postive and sum to 1.
        N (int): Specifies number of particles to sample. Defaults to len(weights)
    Outputs:
        sampled_indices: array of length N of indices.

    """
    if N is None:
        N = len(weights)

    # Compute evenly spaced values 1/N apart started from u0 ~ np.random.uniform(0, 1/N)
    u0 = np.random.random()
    u = (u0 + np.arange(N)) / N
    
    # Compute cumulative sum
    cumulative_w = np.cumsum(weights)
    cumulative_w[-1] = 1

    # Find sampled indices and return.
    sampled_indices = np.searchsorted(cumulative_w, u)

    return sampled_indices

def normalize_weights(weights):
    """
    Normalize posterior weights to sum to one. Ensure all points have minimum likelihood of being carried forward
    Inputs:
        weights: array of weights
    Output:
        normalized_weights: array of normalized weights
    """

    # Normalize to sum to 1
    weights = weights / np.sum(weights)

    # Return weights
    return weights
