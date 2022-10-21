import numpy as np
import pandas as pd
import time
import random

# Custom Imports
from BACE.user.configuration import likelihood_pdf, theta_parameters, answers, n_starting_points, n_iterations, nsamples, max_time, designs, sample_designs, design_bounds
from BACE.utils import sample_parameters
from BACE.filter_pmc import pmc_filter
from BACE.design_optimization import bayesian_optimization, mutual_information, expected_improvement

def main():

    # Set seed for random and numpy packages.
    seed=42
    random.seed(seed)
    np.random.seed(seed)

    print("Starting main...")

    # Specify simulation parameters
    simulation_parameters = {
        "n_sims": 75, # Number of simulations per method
        "n_samples": nsamples, # Number of samples for thetas population
        "n_designs_per_sim": 25, # Total number of designs shown to respondents per simulation
        "J": 5,
        "max_time": max_time,
        "file_out": "./simulation_output/simulation.csv" # File name for output csv
    }

    # Specify different types of simulations
    simulation_methods = [
        # BACE Method
        {
            "label": "BACE",
            "optimization": "bayesian",
            "n_starting_points": n_starting_points,
            "n_iterations": n_iterations
        },
        # Random design
        {
            "label": "Random",
            "optimization": "random",
            "n_starting_points": "NA",
            "n_iterations": "NA"
        }
    ]

    # Perform simulation
    simulation_output = simulation(theta_parameters, designs, simulation_parameters, simulation_methods)
    simulation_output.to_csv(simulation_parameters["file_out"])

def simulation(theta_parameters, designs, simulation_parameters, simulation_methods):

    print("Starting simulation...")

    # Initialize output DataFrame
    output = pd.DataFrame()
    i = 0

    for _ in range(simulation_parameters["n_sims"]):

        # Draw true theta
        true_theta = sample_parameters(theta_parameters, 1)

        # Create dataframe of true values with simulation_parameters["n_designs_per_sim"] rows.
        true_thetas = pd.concat([true_theta] * simulation_parameters["n_designs_per_sim"], ignore_index=True)

        # Initialize empty arrays to store information for sim_no
        for method_parameters in simulation_methods:

            # Sample thetas to form prior distribution
            thetas = sample_parameters(theta_parameters, simulation_parameters["n_samples"])

            # Create empty objects to store information
            round_no, observed_answers, true_answers, time_history = [], [], [], []
            design_history, estimate_history = [], pd.DataFrame()

            for j in range(simulation_parameters["n_designs_per_sim"]):

                # Record start time for round j.
                start_round = time.time() 

                # Calculate next design.
                _, next_design = calculate_next_design(thetas, designs, answers, likelihood_pdf, method_parameters, simulation_parameters["max_time"])

                # Evaluate observed and true answers
                observed_answer, true_answer = get_answers(answers, true_theta, next_design, likelihood_pdf)

                # Update design and answer histories
                if j == 0:
                    design_history = [next_design]
                else:
                    design_history = np.concatenate((design_history, [next_design]), axis=0)

                observed_answers.append(observed_answer)

                # Perform Inference
                thetas =  pmc_filter(
                    thetas=thetas,
                    design_history=design_history,
                    answer_history=observed_answers,
                    likelihood_pdf=likelihood_pdf,
                    theta_parameters=theta_parameters,
                    N=simulation_parameters["n_samples"],
                    J=simulation_parameters["J"]
                )
                                                    
                # Record end time for round j.
                end_round = time.time()

                # Calculate estimates
                estimates = mean_estimates(thetas)

                # Store additional information for output
                round_no.append(j)
                true_answers.append(true_answer)
                time_history.append(end_round - start_round)
                estimate_history = pd.concat([estimate_history, estimates], ignore_index=True)
       
            # Combine information for simulation round into single DataFrame
            round_df = combine_round_info(true_thetas, round_no, observed_answers, true_answers, time_history, method_parameters, design_history, estimate_history)
            round_df["sim_no"] = i

            # Concatenate round information to output DataFrame
            output = pd.concat([output, round_df], ignore_index=True)

            # Store temporary csv as output since simulation can take long
            output.to_csv(simulation_parameters["file_out"])

            print(f"Finished round {i} of {simulation_parameters['n_sims'] * len(simulation_methods)}. Avg. Time per QuestionRound Time: {np.mean(time_history)}s.")
            i += 1
    
    return output

def combine_round_info(true_thetas, round_no, observed_answers, true_answers, time_history, method_parameters, design_history, estimate_history):

    # Generate starting DataFrame with true parameter values
    output = true_thetas.rename(columns = lambda x: '_'.join(['true', x]))

    # Update columns for output.
    output['round_no'] = round_no
    output['observed_answer'] = observed_answers
    output['true_answer'] = true_answers
    output['time_round'] = time_history

    # Incorporate method information
    output['label'] = method_parameters["label"]
    output['optimization'] = method_parameters["optimization"]
    output['n_starting_points'] = method_parameters["n_starting_points"]
    output['n_iterations'] = method_parameters["n_iterations"]

    design_history = pd.DataFrame(design_history, columns = ["d_" + str(i) for i in range(design_history.shape[1])])
    output = pd.concat([output, design_history], axis=1)
    output = pd.concat([output, estimate_history], axis=1)

    return output

def calculate_next_design(thetas, designs, answers, likelihood_pdf, method_parameters, max_time):

    if method_parameters['optimization'] == 'bayesian':

        next_index, next_design = bayesian_optimization(
            thetas=thetas, 
            designs=designs, 
            answers=answers, 
            likelihood_pdf=likelihood_pdf, 
            acquisition_f=expected_improvement, 
            n_starting_points=method_parameters["n_starting_points"], 
            n_iterations=method_parameters["n_iterations"],
            max_time=max_time,
            )

    elif method_parameters['optimization'] == 'brute_force':

        # Calculate mutual information for selected designs
        mutual_info = {d_index: mutual_information(thetas, answers, likelihood_pdf, designs.loc[d_index, :]) for d_index in designs.index}

        # Find index for design with highest mutual information.
        best_index = max(mutual_info, key=mutual_info.get)
        
        next_index = best_index
        next_design = designs.loc[best_index, ]

    else:

        if method_parameters['optimization'] != 'random':
            print("Optimization method not specified. Defaulting to randomly chosen design.")

        #next_index = np.random.choice(len(designs))
        next_index = 0
        next_design = sample_designs()[0]

    return next_index, next_design

def get_answers(answers, thetas, design, likelihood_pdf):

    weights = [float(likelihood_pdf(answer, thetas, design)) for answer in answers]

    # Observed answer chosen based on likelihood
    observed_answer = np.random.choice(answers, p=weights)

    # Answer with highest likelihood of being chosen
    true_answer = answers[np.argmax(weights)]

    return observed_answer, true_answer

def mean_estimates(thetas):

    # Compute mean for each column. Convert to DataFrame.
    thetas = thetas.mean().to_frame().T

    # Rename columns
    rename_cols = { theta: 'mean_' + theta for theta in thetas }
    thetas.rename(columns=rename_cols, inplace=True)

    return thetas

if __name__ == '__main__':
    main()
    print('Finished simulation')