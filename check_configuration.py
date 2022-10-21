import numpy as np
import time
import traceback

import BACE.user.configuration
import BACE.utils
import BACE.filter_pmc
import BACE.design_optimization

def main():

    # Number of test runs for Bayesian Optimization and PMC inference.
    n_opt_attempts = 100

    # Check that all elements in `answers` are integers.
    BACE.utils.check_answers(BACE.user.configuration.answers)

    # Attempt to generate designs dataframe.
    designs = BACE.utils.check_designs(BACE.user.configuration.generate_designs_dataframe)

    # Check thata alal elements in `theta_parameters` are specified correctly.
    BACE.utils.check_thetas(BACE.user.configuration.theta_parameters)

    # Sample from prior distribution
    thetas = BACE.utils.sample_parameters(
        parameters=BACE.user.configuration.theta_parameters,
        nsamples=BACE.user.configuration.nsamples
    )
    assert len(thetas) == BACE.user.configuration.nsamples, "Incorrect number of parameters sampled from `theta_parameters`."

    # Compute likelihood_pdf(answer | thetas, design) for every design in designs.
    BACE.utils.check_likelihood(
        answers=BACE.user.configuration.answers,
        thetas=thetas,
        designs=designs,
        likelihood_pdf=BACE.user.configuration.likelihood_pdf
    )

    # Perform erations of pmc_filter and bayesian_optimization, which are used to select optimal questions.

    size_history = np.random.randint(low=1, high=10, size=n_opt_attempts)
    pmc_flag, bopt_flag = False, False
    pmc_error_message, bopt_error_message = "", ""

    start_time = time.time()
    for i in range(n_opt_attempts):

        try:
            test_thetas = BACE.filter_pmc.pmc_filter(
                thetas=thetas,
                design_history = designs.sample(size_history[i], replace=True),
                answer_history = np.random.choice(BACE.user.configuration.answers, size=size_history[i], replace=True),
                likelihood_pdf=BACE.user.configuration.likelihood_pdf,
                theta_parameters=BACE.user.configuration.theta_parameters,
                N=BACE.user.configuration.nsamples
            )
        except Exception:
            test_thetas = BACE.utils.sample_parameters(BACE.user.configuration.theta_parameters, BACE.user.configuration.nsamples)
            pmc_flag = True
            pmc_error_message = traceback.format_exc()



        try:
            BACE.design_optimization.bayesian_optimization(
                thetas=test_thetas,
                designs=designs,
                answers=BACE.user.configuration.answers,
                likelihood_pdf=BACE.user.configuration.likelihood_pdf,
                max_time=BACE.user.configuration.max_time
            )
        except Exception:
            bopt_flag = True
            bopt_error_message = traceback.format_exc()

    end_time = time.time()

    message_from_flag("`pmc_filter()`", pmc_flag, pmc_error_message)
    message_from_flag("`bayesian_optimization()", bopt_flag, bopt_error_message)
    print(f"Average time per question: {np.round((end_time - start_time) / n_opt_attempts, decimals=4)}s")

def message_from_flag(label, flag, error_message):

    if flag:
        print(f"Error produced in {label}. Error provided below.")
        print(error_message)
    else:
        print(f"No errors detected in {label}.")

if __name__=="__main__":
    main()