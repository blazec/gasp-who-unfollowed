import json

CONFIG_FILE_PATH =  './config.json'

def get_config():
    return read_config_from_json_file(CONFIG_FILE_PATH)

def read_config_from_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)
