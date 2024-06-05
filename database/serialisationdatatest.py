import os
import json
import datetime

serialisationFile = os.path.join(os.path.dirname(__file__), 'data.json')

def serialisation_data():
    f = open('data.json')
    data = json.load(f)
    # print(data)
    return data

# print(serialisation_data)
f = open('serialisation.json')
sentiment_chart_dict = json.load(f)
# print(sentiment_chart_dict)
# pickle.dump(data, f)

def serialize_custom(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to string in ISO format
    # Handle other custom objects here if needed
    raise TypeError("Object of type '{}' is not JSON serializable".format(type(obj)))

def print_types():
    try:
        for key, value in sentiment_chart_dict.items():
            # print(key)
            # print(value)
            try:
                json.dumps({key: value})
                print(json.dumps({key: value}))
            except TypeError as e:
                print(f"Serialization error for key '{key}': {e}")
        return sentiment_chart_dict            
    except TypeError as e:
        # If there's a serialization error, log or handle it
        print(f"Serialization error: {e}")
        return {"error": "Data serialization failed due to non-serializable content"}

# print("Here results = ", print_types())