# External packages
from mango import scheduler, Tuner
import numpy as np
import time

# Local Imports
from bace.user_config import size_thetas, answers, theta_params, design_params, conf_dict, likelihood_pdf, max_opt_time
#from bace.bace_utils import sample_thetas
import bace.bace_utils
from bace.information_criteria import mutual_information

# Set it up so optimization stops after bace.user_config.max_opt_time seconds
class context:
    start_time=None
    thetas=None
    max_opt_time=max_opt_time

def early_stop(results):

    if context.start_time is None:
        context.start_time = time.time()
    else:
        time_elapsed = time.time() - context.start_time
        if time_elapsed > context.max_opt_time:

            print(f'Stopping early due to max_opt_time exceeded. \
                time_elapsed={time_elapsed} \
                max_opt_time={context.max_opt_time}')
            return True
    return False

# Specify optimizer
@scheduler.serial
def objective(**design):
    return mutual_information(
        thetas=context.thetas,
        answers=answers,
        likelihood_pdf=likelihood_pdf,
        **design
    )

conf_dict['early_stopping'] = early_stop
design_tuner = Tuner(design_params, objective, conf_dict)

def get_next_design(thetas, tuner=design_tuner):
    context.start_time=None
    context.thetas=thetas.copy()
    return tuner.maximize()['best_params']