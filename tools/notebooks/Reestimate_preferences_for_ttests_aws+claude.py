# Import pandas
import pandas as pd
import hashlib
import numpy as np

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

from app.bace.user_config import theta_params, likelihood_pdf, size_thetas

# Base path for output files — three CSVs will be written here
output_dir = r"/workspaces/bace/app/bace/"

def clean_designs_and_answers(item, answers, slice_start=None, slice_end=None):
    """
    Returns cleaned design and answer histories, optionally sliced to a
    specific window of responses.

    slice_start : int or None — first response to include (0-indexed, inclusive).
                  None means start from the beginning.
    slice_end   : int or None — last response to include (0-indexed, exclusive).
                  None means go to the end.

    Examples:
        Responses 1-10  → slice_start=0, slice_end=10
        Responses 11-20 → slice_start=10, slice_end=20
        Responses 1-20  → slice_start=None, slice_end=None  (original behaviour)
    """
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

    # Apply the window slice after cleaning
    design_history = design_history[slice_start:slice_end]
    answer_history = answer_history[slice_start:slice_end]

    return design_history, answer_history

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

def get_pmc_seed(profile_id: str) -> int:
    """Convert a profile UUID to a stable integer seed for numpy."""
    return int(hashlib.md5(profile_id.encode()).hexdigest(), 16) % (2**31)


def run_estimation_window(db_items, answers, slice_start, slice_end, estimation_version):
    """
    Runs PMC estimation for all respondents using only the responses
    in [slice_start, slice_end) and returns a tidy DataFrame.

    Parameters
    ----------
    db_items          : list of DynamoDB items (already fetched)
    answers           : answer options from user_config
    slice_start       : int or None — start of response window (0-indexed, inclusive)
    slice_end         : int or None — end of response window (0-indexed, exclusive)
    estimation_version: str — label stored in the output CSV
    """
    output = []

    for item in db_items:

        item = decimal_to_float(item)

        design_history, answer_history = clean_designs_and_answers(
            item, answers,
            slice_start=slice_start,
            slice_end=slice_end
        )
        ND = len(design_history)

        # Skip respondents with no valid answers in this window
        if ND == 0:
            continue

        profile_id = item.get("profile_id")

        try:
            np.random.seed(get_pmc_seed(profile_id))
            posterior_thetas = pmc(
                theta_params,
                answer_history,
                design_history,
                likelihood_pdf,
                size_thetas,
                J=5
            )
            estimates = posterior_thetas.agg(['mean', 'median', 'std']).to_dict()
            reestimation_successful = 1

        except Exception as e:
            print(f"  Error for {profile_id}: {e}")
            reestimation_successful = 0
            estimates = {}

        output.append({
            "profile_id": profile_id,
            "estimation_version": estimation_version,
            "n_designs": ND,
            "reestimation_successful": reestimation_successful,
            **estimates
        })

    return pd.json_normalize(output)


# ── Define the three windows ──────────────────────────────────────────────────
windows = [
    # (slice_start, slice_end, version_label,       output_filename)
    (None, 10,   "PMC_reestimation_q1_10",  "reestimation_q1_10_pol.csv"),
    (10,   20,   "PMC_reestimation_q11_20", "reestimation_q11_20_pol.csv"),
    (None, None, "PMC_reestimation_q1_20",  "reestimation_q1_20_pol.csv"),
]

# ── Run and save ──────────────────────────────────────────────────────────────
for slice_start, slice_end, version, filename in windows:
    print(f"Running window: {version} ...", end=" ")
    df = run_estimation_window(
        db_items, answers,
        slice_start=slice_start,
        slice_end=slice_end,
        estimation_version=version
    )
    out_path = os.path.join(output_dir, filename)
    df.to_csv(out_path, index=False)
    print(f"done — {len(df)} respondents saved to {filename}")

print("\nAll three windows complete.")

for filename in ["reestimation_q1_10.csv", "reestimation_q11_20.csv", "reestimation_q1_20.csv"]:
    df = pd.read_csv(os.path.join(output_dir, filename))
    successful = df['reestimation_successful'].sum()
    print(f"{filename}: {len(df)} respondents total, {successful} successful estimations")
