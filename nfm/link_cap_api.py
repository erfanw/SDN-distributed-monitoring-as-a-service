import json


def get_link_capacity():
    with open('link_cap.json') as json_file: 
        link_cap = json.load(json_file)
    return link_cap
