from decimal import Decimal
import json
import pandas as pd

# Update JSONEncoder to handle dynamodb decimal type
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

# Format response to econde output as json
def format_response(data, code=200, content_type={'Content-Type': 'application/json'}):
    return json.dumps(data, cls=DecimalEncoder), code, content_type

# Get parameters from web request
def get_request(request):

    content_type = request.headers.get('Content-Type')
    if request.method=='GET':
        output = request.args
    else:
        if (content_type == 'application/json'):
            output = request.get_json()
        else:
            output = request.form.to_dict()
    
    return output

# Function to sample from the prior distribution
def sample_thetas(theta_params, N):
    return pd.DataFrame({
        key: dist.rvs(size=N) for key, dist in theta_params.items()
    })