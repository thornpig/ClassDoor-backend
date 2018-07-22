import json
from calendar import monthrange
from datetime import datetime, timedelta 


def print_json(json_data):
    print(json.dumps(json.loads(json_data), sort_keys=True,
                     indent=4, separators=(',', ': ')))
