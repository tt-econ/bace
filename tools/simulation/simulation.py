import numpy as np
import pandas as pd
import time
import random
from IPython.utils.capture import capture_output
from mango import Tuner

# For getting parent's module
import os, sys, importlib
from pathlib import Path

def main(sim_params):
    print("Starting main...")

    # Perform simulation
    simulation_output = simulation(
        sim_params=sim_params,
        sim_methods=get_sim_methods()
    )
    simulation_output.to_csv(sim_params["file_out"])

def get_sim_methods():

    objective = design_optimization.get_objective(user_config.answers, user_config.likelihood_pdf)
    config = design_optimization.get_conf_dict(user_config.conf_dict)

    config_random = config.copy()
    config_random['optimizer'] = 'Random'

    tuner_bace = Tuner(
        user_config.design_params,
        objective,
        config
    )
    tuner_rand = Tuner(
        user_config.design_params,
        objective,
        config_random
    )

    # Specify different types of simulations
    sim_methods = [
        dict(
            opt_type="BACE",
            search_type="bayesian",
            random_design=False,
            design_tuner=tuner_bace
        ),
        # Random search
        # dict(
        #     opt_type="BACE",
        #     search_type="random",
        #     random_design=False,
        #     design_tuner=tuner_rand
        # ),
        dict(
            opt_type="RAND",
            search_type="random",
            random_design=True,
            design_tuner=tuner_bace
        ),
    ]

    return sim_methods

def simulation(sim_params, sim_methods):

    # Initialize output DataFrame
    print("Starting simulation...")
    output = pd.DataFrame()
    i = 0

    for _ in range(sim_params["n_sims"]):


        # Sample true thetas from prior distribution
        true_theta = pmc_inference.sample_thetas(
            sim_params.get('theta_params'),
            1
        )

        # Create dataframe of true values with sim_params["n_designs_per_sim"] rows.
        true_thetas = pd.concat(
            [true_theta] * sim_params.get('n_designs_per_sim'),
            ignore_index=True
        )

        context = sim_params.get('context')
        # Initialize empty arrays to store information for sim_no
        for method in sim_methods:
            context.start_time = None
            context.thetas = None

            # Sample thetas to form prior distribution
            thetas = pmc_inference.sample_thetas(
                sim_params.get('theta_params'),
                sim_params.get('size_thetas')
            )

            # Create empty objects to store information
            round_no, observed_answers, true_answers, time_history = [], [], [], []
            design_history, estimate_history = [], pd.DataFrame()

            for j in range(sim_params.get('n_designs_per_sim')):

                start_round = time.time() # Record start time for round.

                # Calculate next design.
                with capture_output():
                    next_design = calculate_next_design(
                        design_tuner=method.get('design_tuner'),
                        thetas=thetas.copy(),
                        random_design=method.get('random_design')
                    )


                # Evaluate observed and true answers
                observed_answer, true_answer = get_answers(
                    answers=user_config.answers,
                    true_theta=true_theta,
                    design=next_design,
                    likelihood_pdf=user_config.likelihood_pdf
                )

                # Update design and answer histories
                design_history.append(next_design)
                observed_answers.append(observed_answer)

                # Update posterior
                thetas = pmc_inference.pmc(
                    theta_params=sim_params.get('theta_params'),
                    answer_history=observed_answers,
                    design_history=design_history,
                    likelihood_pdf=user_config.likelihood_pdf,
                    N=sim_params.get('size_thetas'),
                    J=sim_params.get('J')
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
            round_df = combine_round_info(true_thetas, round_no, observed_answers, true_answers, time_history, method, design_history, estimate_history)
            round_df["sim_no"] = i

            # Concatenate round information to output DataFrame
            output = pd.concat([output, round_df], ignore_index=True)

            # Store temporary csv as output since simulation can take long
            output.to_csv(sim_params["file_out"])

            print(f"Finished round {i+1} of {sim_params['n_sims'] * len(sim_methods)}. Avg. Time per QuestionRound Time: {np.mean(time_history)}s.")
            i += 1

    print_estimates(output, user_config.theta_params)

    return output

def combine_round_info(true_thetas, round_no, observed_answers, true_answers, time_history, method, design_history, estimate_history):

    # Generate starting DataFrame with true parameter values
    output = true_thetas.rename(columns = lambda x: '_'.join(['true', x]))

    # Update columns for output.
    output['round_no'] = round_no
    output['observed_answer'] = observed_answers
    output['true_answer'] = true_answers
    output['time_round'] = time_history

    for key, val in method.items():
        if key != "design_tuner":
            output[key] = val

    output = pd.concat([output, pd.DataFrame(design_history), estimate_history], axis=1)

    return output

def print_estimates(output, theta_params):

    final_rows = output[output['round_no'] == sim_params.get('n_designs_per_sim')-1]
    final_rows = final_rows.groupby(['opt_type', 'search_type'])

    for param in theta_params:

        print(f'Parameter: {param}')

        print('MSE')
        print(final_rows.apply(lambda df: np.mean((df[f'mean_{param}'] - df[f'true_{param}'])**2)).reset_index())

        print('MAE')
        print(final_rows.apply(lambda df: np.mean(df[f'mean_{param}'] - df[f'true_{param}'])).reset_index())

def get_random_design(design_tuner):

    next_design = design_tuner.ds.get_random_sample(size=1)
    while len(next_design) < 1:
        next_design = design_tuner.ds.get_random_sample(size=1)

    return next_design[0]

def calculate_next_design(design_tuner, thetas, random_design=False):

    if random_design:
        next_design = get_random_design(design_tuner)
    else:

        next_design = design_optimization.get_next_design(
            thetas=thetas.copy(),
            tuner=design_tuner
        )

    return next_design

def get_answers(answers, true_theta, design, likelihood_pdf):

    # Likelihood of choosing each answer
    w = [float(likelihood_pdf(answer, true_theta, design)) for answer in answers]

    # Select observed answer
    observed_answer = np.random.choice(answers, p=w)

    # Answer with highest likelihood of being chosen
    true_answer = answers[np.argmax(w)]

    return observed_answer, true_answer

def mean_estimates(thetas):

    # Compute mean for each column. Convert to DataFrame.
    thetas = thetas.mean().to_frame().T

    # Rename columns
    rename_cols = { theta: 'mean_' + theta for theta in thetas }
    thetas.rename(columns=rename_cols, inplace=True)

    return thetas

def import_parents(level=1):
    global __package__
    file = Path(os.path.abspath('')).resolve()
    parent, top = file.parent, file.parents[level - 1]

    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError: # already removed
        pass

    __package__ = '.'.join(parent.parts[len(top.parts):])
    importlib.import_module(__package__) # won't be needed after that

if __name__ == '__main__' and __package__ is None:

    import_parents(level=2)

    # BACE Imports
    import app.bace.pmc_inference as pmc_inference
    import app.bace.user_config as user_config
    import app.bace.design_optimization as design_optimization

    ###############################
    # Specify Simulation Parameters

    N_sims = 200 # Number of simulated individuals per optimization type
    N_designs_per_sim = 25 # Number of questions per simulation

    ###############################

    # Set true_params distributions to draw from, default to the prior
    true_params = user_config.theta_params

    context = design_optimization.context

    # Simulation Parameters
    sim_params = dict(
        n_sims=N_sims,
        size_thetas=user_config.size_thetas,
        n_designs_per_sim=N_designs_per_sim,
        theta_params=user_config.theta_params,
        true_params=true_params,
        J=5,
        context = context,
        file_out='./simulation_output/simulation.csv'
    )

    # Set seed for random and numpy packages.
    seed = 42
    random.seed(seed)
    np.random.seed(seed)

    main(sim_params=sim_params)
    print('Finished simulation')
