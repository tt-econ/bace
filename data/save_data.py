import boto3
import os
import pandas as pd

####### Output FILE ########

file_name = 'dynamodb_contents.csv' # Location for output file
id_column = 'profile_id' # Unique ID column for each profile
table_name = 'profiles' # Update this if the name of the db table in template.yaml is changed

############################

# Construct the absolute file path based on the current file's location
script_dir = os.path.dirname(__file__)
file_out = os.path.join(script_dir, file_name)

# Store database connection
ddb = boto3.resource('dynamodb')
table = ddb.Table(table_name)

# Scan all data from DyanmoDB table and save as data frame
data = pd.DataFrame(table.scan()['Items'])
df = pd.DataFrame(data)

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