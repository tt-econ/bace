#!/usr/bin/env python
# coding: utf-8

# # Notebook for Reestimating Preference Parameters Using Experimental Data
# 
# This notebook allows you to reestimate preference parameters using the full experimental data for each subject.
# 
# You can use the original prior distribution and likelihood specification, or you can specify a new prior or choice model that you would like to estimate.
# 
# Begin by importing the required packages and BACE functions.

# In[10]:


# Import pandas
import pandas as pd

import os, sys, importlib
from pathlib import Path

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

import_parents(level=2)

# Import database connection and pmc function
from app.database.db import table, decimal_to_float
from app.bace.pmc_inference import pmc
from app.bace.user_config import answers


# To reestimate preference parameters using the existing BACE specifications, you can run the following line:
# 
# ```
# from bace.user_config import theta_params, likelihood_pdf, size_thetas
# ```
# 
# Alternatively, you can specify each of the following parameters using the same process that you used to define the components in `app/bace/user_config.py`:
# - `theta_params`: Specifies the prior distribution.
# - `likelihood_pdf`: Specify the likelihood of observing each answer in answers.
# - `size_thetas`: The size of the sample drawn from `theta_params`. Since speed is less important outside of an experiment, you can improve the precision of estimates by increasing this number.
# 
# Note that the choice model defined in `likelihood_pdf` can depend on new preference parameters in `theta_params` or combinations of the original design components that an individual saw.
# 
# In this example, we will use the existing BACE specifications.

# In[11]:


from app.bace.user_config import theta_params, likelihood_pdf, size_thetas


# Now, specify `estimation_version` with notes that you want to record in the output file, and specify `output_file` with the path that you want to use to save your `.csv`.

# In[ ]:


# Notes to store in output file
estimation_version = "PMC_reestimation"

# Output file path.
output_file = r"/workspaces/bace/app/bace/reestimation.csv"


# The following function is used to clean the design and answer histories for each individual in the database.
# 
# It ensures that the design and answer histories are the same length for re-estimation; these can differ if, for example, an individual exited the survey early.

# In[13]:


def clean_designs_and_answers(item, answers):

    str_answers = [str(answer) for answer in answers]

    design_hist = item['design_history'].copy()
    answer_hist = item['answer_history'].copy()
    answer_hist.extend([None] * (len(design_hist) - len(answer_hist)))

    # Store Output
    design_history = []
    answer_history = []


    for design, answer in zip(design_hist, answer_hist):

        if (design is not None) and (answer is not None) and (str(answer) in str_answers):

            design_history.append(design)
            answer_history.append(answer)

    return design_history, answer_history


# The following code queries your database for all items. Each item contains all information for an individual survey respondent, which is characterized by a unique `profile_id`.
# 
# Note: You can also modify the code to get the data from a csv file after using `/data/save_data.py` instead of querying from the server.

# In[14]:


import boto3

id_column = 'profile_id' # Unique ID column for each profile
table_name = 'bace-db' # Update this if the name of the database TableName in template.yaml is changed
# Update `table_region` below to the region created with `sam deploy --guided`, saved in the SAM configuration file (samconfig.toml by default)
#   if different from the default region in ~/.aws/config (or C:\Users\USERNAME\.aws\config)
table_region = boto3.Session().region_name # example if different from default: table_region = 'us-east-2'
# os.environ['AWS_PROFILE'] = "YOUR_AWS_PROFILE_NAME" # Set this if your current AWS login profile is not the default one -- see profiles in ~/.aws/config (or C:\Users\USERNAME\.aws\config)

############################

# Start database connection
ddb = boto3.resource('dynamodb', region_name = table_region)
table = ddb.Table(table_name)

# Scan all data from DynamoDB table
response = table.scan()
db_items = response['Items']

# Go beyond the 1mb limit: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Scan.html
while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    db_items.extend(response['Items'])


# For each item, the script reestimates preference parameters using the new prior distribution and choice model that you have specified.
# 
# An individual's IDs, the number of questions used for re-estimation, and preference estimates are exported in a csv.

# In[ ]:


output = []

for item in db_items:

    # Conver DynamoDB Decimal type to floats
    item = decimal_to_float(item)

    # Get cleaned design and answer histories.
    design_history, answer_history = clean_designs_and_answers(item, answers)
    ND = len(design_history)

    # Estimate preferences if the individual answered at least one question.
    if ND > 0:

        try:

            #################################################################################
            ### Edit this block to update the method for calculating posterior estimates. ###
            #################################################################################


            # Compute posterior estimates using Population Monte Carlo
            posterior_thetas = pmc(
                theta_params,
                answer_history,
                design_history,
                likelihood_pdf,
                size_thetas,
                J=5
            )

            # Calculate the mean and median posterior estimate for each parameter.
            # Update this code to store alternative statistics.
            estimates = posterior_thetas.agg(['mean', 'median','std']).to_dict()

            #############################################################################
            #############################################################################

            reestimation_successful = 1


        except:

            # What do you want to happen if the re-estimation triggers an error?
            reestimation_successful = 0
            estimates = {}

        # Store output.
        # You can add additional variables associated with an item using item.get('var') to the exported csv.
        individual_output = {
            "profile_id": item.get("profile_id"),
            "estimation_version": estimation_version,
            "n_designs": ND,
            "reestimation_successful": reestimation_successful,
            **estimates
        }

        output.append(individual_output)


# Convert output to dataframe and write to .csv
output_df = pd.json_normalize(output)
output_df.to_csv(output_file, index=False)


# Note that you can update this code block above to adjust other components of the reestimation.
# 
# For example, the notebook defaults to using Population Monte Carlo to reestimate preferences.
# 
# If you want to estimate preferences using an alternative method, you can update the following block. For example, you could perform logistic regression using each individual's data or you can use an alternative method to perform Bayesian Inference.
# 
# You can also edit what statistics are saved when forming estimates.
# 
# ```python
# #############################################################################
# ### Edit this block to update the method for calculating posterior estimates.
# #############################################################################
# 
# # Compute posterior estimates using Population Monte Carlo
# posterior_thetas = pmc(
#     theta_params, 
#     answer_history, 
#     design_history, 
#     likelihood_pdf, 
#     size_thetas,
#     J=5
# )
# 
# # Calculate the mean and median posterior estimate for each parameter.
# # Update this code to store alternative statistics.
# estimates = posterior_thetas.agg(['mean', 'median']).to_dict()
# 
# #############################################################################
# #############################################################################
# ```
# 
# We hope this notebook is useful for recomputing preference estimates after an experiment.
