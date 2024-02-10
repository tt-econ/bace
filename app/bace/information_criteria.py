# Requirements
import numpy as np

# Specify objective function - Mutual Information
def mutual_information(thetas, 
                       answers, 
                       likelihood_pdf, 
                       **design_params):
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
        likelihood = likelihood_pdf(answer, thetas, **design_params)
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