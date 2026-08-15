# External packages
from mango import scheduler, Tuner
import numpy as np
import time

# Set it up so optimization stops after max_opt_time seconds
class context:
    max_opt_time=5 # default is 5 seconds if unchanged
    start_time=None
    thetas=None

# =====================================================================
# RESERVED ANCHOR ROUNDS  (fix for beta_satellite starvation)
# ---------------------------------------------------------------------
# BACE is greedy/one-step (paper Prop 3), so every round the moral params
# (m0/m1) win the info competition and the assessor contrast is never
# served -> beta_satellite stays at its prior. On the rounds listed below
# we OVERRIDE selection and serve a fixed Satellite-vs-clean-Human menu at
# MATCHED error with no bribe on either side. Then money cancels and
#     U_sat - U_human = beta_satellite   exactly,
# i.e. the choice is a pure logit read on beta_satellite. This is the same
# menu BACE would pick if it were optimising beta_satellite alone (Thm 1),
# so it's not a hack; and the posterior update downstream is IDENTICAL
# either way -- it conditions on (design, answer) regardless of how the
# design was chosen (paper Eq. 2). We only override SELECTION, not inference.
#
# ---- SET THESE TWO THINGS ----
# 1) RESERVED_ROUNDS must match HOW YOUR DRIVER COUNTS rounds. If your caller
#    passes question_number = len(profile['design_history']), that is
#    0-INDEXED (first question = 0) -> use e.g. [0, 4, 9].
#    If it passes a 1-indexed question number -> use [1, 5, 10].
# 2) Keep it to ~3-4 rounds and spread them out. One early (to seed), the
#    rest later (after m0/m1 have tightened). Do NOT over-reserve or you
#    starve the moral parameters instead.
RESERVED_ROUNDS   = [1, 5]   # <-- edit to match your driver's counter
ANCHOR_ERROR      = 0.0          # matched error on BOTH sides (cancels). 0 = "correct bill".
ANCHOR_K          = 1.2          # irrelevant (bribe=0), just a valid value

def _is_reserved(question_number):
    return question_number is not None and question_number in RESERVED_ROUNDS

def _anchor_menu(question_number, profile=None):
    # Satellite vs clean Human, matched error, no bribe on either side.
    # Alternate which SIDE is the satellite across reserved rounds to cancel
    # any left/right (A/B position) response bias.
    idx = RESERVED_ROUNDS.index(question_number)
    sat_on_a = (idx % 2 == 0)
    a_ass, b_ass = ('Satellite', 'Human') if sat_on_a else ('Human', 'Satellite')
    return dict(
        error_a=ANCHOR_ERROR, error_b=ANCHOR_ERROR,
        bribe_a=0.0,          bribe_b=0.0,
        k_a=ANCHOR_K,         k_b=ANCHOR_K,
        assessor_a=a_ass,     assessor_b=b_ass,
    )
# =====================================================================

# early_stopping examples: https://github.com/ARM-software/mango/blob/main/examples/EarlyStopping.ipynb
def early_stop(results):

    if context.start_time is None:
        context.start_time = time.time()
    else:
        time_elapsed = time.time() - context.start_time
        if time_elapsed > context.max_opt_time:

            print(f'Stopping early due to max_opt_time (seconds) exceeded. \
                time_elapsed={time_elapsed} \
                max_opt_time={context.max_opt_time}')
            return True
    return False

def get_objective(answers, likelihood_pdf, profile=None):
    # Specify optimizer
    @scheduler.serial
    def objective(**design):
        return mutual_information(
            thetas=context.thetas,
            answers=answers,
            likelihood_pdf=likelihood_pdf,
            design=design,
            profile=profile
        )
    return objective

def get_conf_dict(conf_dict):
    conf_dict['early_stopping'] = early_stop
    return conf_dict

def get_design_tuner(design_params, objective, conf_dict):
    design_tuner = Tuner(design_params, objective, conf_dict)
    return design_tuner

def get_next_design(thetas, tuner, question_number=None, profile=None):
    # RESERVED-ROUND INTERCEPT: on the listed rounds, serve the fixed assessor
    # anchor instead of running Bayesian optimization. Returns the same dict
    # shape as tuner.maximize()['best_params'], so everything downstream
    # (convert_design, likelihood, PMC update) is unchanged.
    # Backwards-compatible: if question_number is not passed, behaves exactly
    # as before (pure adaptive).
    if _is_reserved(question_number):
        return _anchor_menu(question_number, profile)

    context.start_time=None
    context.thetas=thetas.copy()
    return tuner.maximize()['best_params']

# Specify objective function - Mutual Information
def mutual_information(thetas,
                       answers,
                       likelihood_pdf,
                       design,
                       profile=None):
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
        likelihood = likelihood_pdf(answer, thetas, design, profile)
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