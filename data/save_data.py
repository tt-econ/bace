import boto3
import os
import pandas as pd

####### Output FILE ########

file_name = 'dynamodb_contents.csv' # Location for output file (relative to this file)
id_column = 'profile_id' # Unique ID column for each profile
table_name = 'bace-db' # Update this if the name of the database TableName in template.yaml is changed
# Update `table_region` below to the region created with `sam deploy --guided`, saved in the SAM configuration file (samconfig.toml by default)
#   if different from the default region in ~/.aws/config (or C:\Users\USERNAME\.aws\config)
table_region = boto3.Session().region_name # example if different from default: table_region = 'us-east-2'
# os.environ['AWS_PROFILE'] = "YOUR_AWS_PROFILE_NAME" # Set this if your current AWS login profile is not the default one -- see profiles in ~/.aws/config (or C:\Users\USERNAME\.aws\config)

############################

# Construct the absolute file path based on the current file's location
script_dir = os.path.dirname(__file__)
file_out = os.path.join(script_dir, file_name)

# Store database connection
ddb = boto3.resource('dynamodb', region_name = table_region)
table = ddb.Table(table_name)

# Scan all data from DynamoDB table and save as data frame
response = table.scan()
data = response['Items']

# Go beyond the 1mb limit: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Scan.html
while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    data.extend(response['Items'])

df = pd.DataFrame(data)

# Remove rows with empty answer history
df = df[~df.answer_history.str.len().eq(0)]

# Expand estimates
if 'estimates' in df.columns:
    estimates_extended = pd.json_normalize(df['estimates']).set_index(df.index)
    df = pd.concat([df.drop('estimates', axis=1), estimates_extended], axis = 1)

# Combine 'answer_history' and 'design_history' into a list column named 'history'
df['history'] = df.apply(lambda x: list(zip(x['answer_history'], x['design_history'])), axis=1)

# Explode the new column 'history' and split into back separate columns: 'answer_history' and 'design_history'
df = df.explode('history')
df[['answer_history', 'design_history']] = pd.DataFrame(df['history'].tolist(), index=df.index)

# Split the 'design_history' column into separate columns
df = pd.concat([df.drop('design_history', axis=1), df['design_history'].apply(pd.Series)], axis=1)

# Add new column 'q_number' to capture the index of the associated question and answer
df['q_number'] = df.groupby([id_column]).cumcount() + 1

# Drop the intermediate column 'history'
df = df.drop('history', axis=1)

# Reset the index to start at 0
df = df.reset_index(drop=True)

df.to_csv(file_out, index=False)  # Save the dataframe as a CSV file
