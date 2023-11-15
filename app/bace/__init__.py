from decimal import Decimal
import json

# Update JSONEncoder to handle dynamodb decimal type
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def format_response(data, code=200, content_type = {'Content-Type': 'application/json'}):
    return json.dumps(data, cls=DecimalEncoder), code, content_type