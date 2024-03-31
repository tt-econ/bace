import json
from decimal import Decimal

# Utilities used by app.py
# Update JSONEncoder to handle dynamodb decimal type
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

# Format response to encode output as json
def format_response(data, code=200, content_type={'Content-Type': 'application/json'}):
    return json.dumps(data, cls=DecimalEncoder), code, content_type

# Get parameters from web request
def get_request(request):

    content_type = request.headers.get('Content-Type')

    if request.method == 'GET':
        output = request.args
    else:
        if content_type == 'application/json':
            output = request.get_json()
        else:
            output = request.form.to_dict()

    return output

# Function to check if the 'answer' key is empty (where empty means no value, None, or an empty string)
def is_answer_empty(answer):
    # Check if 'answer' is None or an empty string
    if answer is None or (isinstance(answer, str) and answer.strip() == ''):
        return True
    # For all other cases, 'answer' is not empty
    return False