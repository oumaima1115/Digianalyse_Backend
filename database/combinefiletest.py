import os
import json

def combine_json_files(*data_sources):
    combined_data = []
    
    for data in data_sources:
        try:
            combined_data.extend(data)
        except Exception as e:
            print(f"Error combining data: {e}")
            continue

    return combined_data
