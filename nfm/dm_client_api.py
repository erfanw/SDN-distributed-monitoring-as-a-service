import json

import requests

URL = "http://localhost:5000/mydb"

def write(data):
    #"ev.message is the message body you want to sent to the DB"
    request = requests.post(URL, json = data)
    return request
    # print(request)
    #prints the result of the request. Eg. "404 nof found"

def select_all(data):
    url = URL + "/" + data
    #"ev.attribute" is a string of the name of the attribute. Eg, "testseries"
    request = requests.get(url)
    return request
    # print(request)
    
def select_last(data):
    url = URL + "/" + data + "/last"
    #"ev.attribute" is a string of the name of the attribute. Eg, "testseries"
    request = requests.get(url)
    # print(request)
    return request

def select_last_second(data):
    url = URL + "/" + data + "/last_second"
    #"ev.attribute" is a string of the name of the attribute. Eg, "testseries"
    request = requests.get(url)
    # print(request)
    return request    
    
def delete(data):
    url = URL + "/" + data
    request = requests.delete(url)
    return request
    # print(request)
