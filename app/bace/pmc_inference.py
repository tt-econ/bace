import scipy.stats
import pandas as pd
import numpy as np

# Function to sample from the prior distribution
def sample_thetas(theta_params, N):
    return pd.DataFrame({
        key: dist.rvs(size=N) for key, dist in theta_params.items()
    })

def pmc(theta_params, answer_history, design_history, likelihood_pdf, N, J=5):

    # Sample from prior distribution
    old_thetas = sample_thetas(theta_params, N)
    scale = 2 * old_thetas.std()

    # Initialize variables to store preference parameters and weights
    pool_thetas = pd.DataFrame()
    w = np.array([])

    for j in range(J):

        # Compute importance weights
        old_thetas, sampled_thetas, weights = importance_sample(old_thetas, theta_params, scale, answer_history, design_history, likelihood_pdf, N)

        # Store sampled points and associated weights
        pool_thetas = pd.concat([pool_thetas, sampled_thetas], ignore_index=True)
        w = np.append(w, weights)

    # Drop index
    pool_thetas.reset_index(drop=True, inplace=True)

    # Return sample of size N from full set of samples and weights
    return systematic_sample(pool_thetas, w/np.sum(w), N=N)

def importance_sample(old_thetas, theta_params, scale, answer_history, design_history, likelihood_pdf, N=None):
    if N is None:
        N = len(old_thetas)

    # Importance sample around existing points.
    new_thetas = pd.DataFrame(
        data = scipy.stats.norm.rvs(size=old_thetas.shape, loc=old_thetas, scale=scale),
        columns = list(old_thetas.columns)
    )

    # Compute importance weight components w = pi / q = lklhd * prior / q
    log_q = compute_q_logpdf(new_thetas, old_thetas, scale)
    log_prior = compute_prior_logpdf(new_thetas, theta_params)
    log_pi = compute_lklhd_logpdf(new_thetas, answer_history, design_history, likelihood_pdf)

    # Calculate weights. Use of M is better for numerical stability.
    log_w = log_pi + log_prior - log_q
    M = np.max(log_w)
    w = np.exp(log_w - M)
    w[np.isnan(w)] = 0

    # Normalize w
    w = w / np.sum(w)

    #next_thetas = new_thetas.sample(n=N, replace=True, weights=w).reset_index(drop=True)
    next_thetas = systematic_sample(new_thetas, w, N)
    return next_thetas, new_thetas, w

def compute_prior_logpdf(thetas, theta_params):
  prior_pdf = np.zeros(len(thetas)) # Initialize zeros
  for param_name, param_dist in theta_params.items():

    param_pdf = param_dist.logpdf(thetas[param_name]) # Compute logpdf of observed values given prior
    prior_pdf += param_pdf

  return prior_pdf

def compute_q_logpdf(new_thetas, old_thetas, scale):
    return np.sum(scipy.stats.norm.logpdf(new_thetas, loc=old_thetas, scale=scale), axis=1)

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
    ND = len(design_history)
    # Initialize lklhd_logpdf
    lklhd_logpdf = 0
    for i in range(ND):
        # Compute p(answer_i | thetas, design_i)
        lklhd = likelihood_pdf(answer_history[i], thetas, **design_history[i])

        with np.errstate(divide='ignore', invalid='ignore'):
            log_lklhd = np.log(lklhd)
            log_lklhd[np.isnan(log_lklhd)] = -np.inf

        lklhd_logpdf += log_lklhd

    return lklhd_logpdf

def systematic_sample(df, weights, N):

    if N is None:
        N = len(df)

    # Compute evenly spaced values 1/N apart started from u0 ~ np.random.uniform(0, 1/N)
    u0 = np.random.random()
    u = (u0 + np.arange(N)) / N

    # Compute cumulative sum
    cumulative_w = np.cumsum(weights)
    cumulative_w[-1] = 1

    # Find indices to keep.
    sampled_indices = np.searchsorted(cumulative_w, u)

    return df.iloc[sampled_indices, :].reset_index(drop=True).copy()
