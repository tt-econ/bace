from decimal import Decimal
import json
import boto3

db_type = 'dynamodb'
table_name = 'bace-db' # Update this if the name of the db table in template.yaml is changed
# Update table_region below to the region name created by `sam deploy --guided`, saved in the SAM configuration file (samconfig.toml by default)
#   if different from the default region in ~/.aws/config (or C:\Users\USERNAME\.aws\config)
table_region = boto3.Session().region_name # example if changed: table_region = 'us-east-2'

# Store database connection
ddb = boto3.resource(db_type, region_name = table_region)
table = ddb.Table(table_name)

# Functions for converting output
def float_to_decimal(data):
    return json.loads(json.dumps(data), parse_float=Decimal)

def decimal_to_float(obj):
    """
    Convert all whole number decimals in 'obj' to integers, convert all sets in lists
    """
    if isinstance(obj, list) or isinstance(obj, set):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

# Update item in database in table.
def update_db_item(table, key, data):

    data = float_to_decimal(data)

    update_expression = 'SET {}'.format(','.join(f'#{k}=:{k}' for k in data))
    expression_attribute_values = {f':{k}': v for k, v in data.items()}
    expression_attribute_names = {f'#{k}': k for k in data}

    response = table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ExpressionAttributeNames=expression_attribute_names,
        ReturnValues='UPDATED_NEW'
    )
