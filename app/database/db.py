from decimal import Decimal
import json

############### Configuration Options ######################

# Specify Name of Database. Required for MongoDB database.
db_name = 'BACE'

# Specify name of DynamoDB table or MongoDB Collection
# If using DynamoDB, this should be the same as the DynamoDB TableName property. 
collection_or_table_name = 'bace-db'

##############################################################
########    Uncomment one of the Following Options    ########
##############################################################


############### Option 1) DynamoDB Version ###################

import boto3
db_type = "dynamodb"

# Update table_region below to the region name created by `sam deploy --guided`, saved in the SAM configuration file (samconfig.toml by default)
#   if different from the default region in ~/.aws/config (or C:\Users\USERNAME\.aws\config)
table_region = boto3.Session().region_name # example if changed: table_region = 'us-east-2'

############# Option 2) MongoDB Local ########################

# import pymongo
# db_type = "mongodb"
# mongodb_host = 'local'
# MONGO_URI = "mongodb://localhost:27017/" # Typical default. Change if hosted at different port on your system.

############# Option 3) MongoDB Atlas (Cloud) ################

# import pymongo
# import certifi

# db_type = "mongodb"
# mongodb_host = 'atlas'
# # (Set username and password as environment variables on the machine/Lambda your function is operating on)
# mongo_username = os.environ.get('mongo_username')
# mongo_password = os.environ.get('mongo_password')

# # Update the connection string.
# # MongoDB Atlas -> Database -> Connect -> Drivers -> Copy and paste connection string here (fix username and password)
# MONGO_URI = f"mongodb+srv://{mongo_username}:{mongo_password}@bacecluster0.uukczpf.mongodb.net/?retryWrites=true&w=majority&appName=BaceCluster0"

##############################################################


def get_db_table(db_type):
 
    if db_type == 'mongodb':

        # Specify code to connect.  
        if mongodb_host == 'local':
            client = pymongo.MongoClient(MONGO_URI)        
        elif mongodb_host == 'atlas':
            client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where()) 
        else:
            print(f'Implement client connection for mongodb_host: {mongodb_host}')
                
        # Ping deployment

        if client.admin.command('ping'):
            print("Pinged your deployment. You successfully connected to MongoDB!")  
        else:
            print('Database failed to connect to MongoDB')

        table = client[db_name][collection_or_table_name]
        
    elif db_type == 'dynamodb':

        # Store database connection
        db_con = boto3.resource(db_type, region_name=table_region)
        table = db_con.Table(collection_or_table_name)
        
    else:
        print("Provided db_type is not mongodb or dynamodb. Update app/database/db.py.")

    return table

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

def check_profile(profile, key):
    if not profile:
        print(f'Profile not found with key: {key}')

def find_item(table, key, db_type):

    if db_type=='mongodb':
        profile = table.find_one(key)
        check_profile(profile, key)
        return profile
    elif db_type == 'dynamodb':
        profile = table.get_item(Key=key).get('Item')
        check_profile(profile, key)
        profile = decimal_to_float(profile)
        return profile
    else:
        print("Provided db_type is not mongodb or dynamodb. Implement find_item for this db_type in app/database/db.py.")


def create_item(table, item, db_type):
    # Put item into database
    if db_type=='mongodb':
        table.insert_one(item)
    elif db_type=='dynamodb':
        table.put_item(Item=float_to_decimal(item))
    else:
        print("Provided db_type is not mongodb or dynamodb. Implement create_item for this db_type in app/database/db.py.")

# Update item in database in table.
def update_dynamodb_item(table, key, data):

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

# Write out code for updating items in MongoDB    
def update_mongodb_item(table, key, data):

    updates = {
        "$set": { k: v for k, v in data.items() } 
    }

    response = table.update_one(key, update=updates)

def update_item(table, key, data, db_type):

    if db_type == 'mongodb':
        update_mongodb_item(table, key, data)
    elif db_type == 'dynamodb':
        update_dynamodb_item(table, key, data)
    else:
        print("Provided db_type is not mongodb or dynamodb. Implement update_item for this db_type in app/database/db.py.")

# Create Database Connection
table = get_db_table(db_type)