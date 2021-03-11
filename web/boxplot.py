import json
import requests

    
def get_data(freq):
    #Real data from our database
    response = _select_all("links_bw")
    data = response.json()
    
    link_util = {}
    aggr_dict = {}

    # for dict in data:
    #     time_split = dict["time"].split(".")[0]
    #     dict["time"] = time_split
    #     if dict['time'] not in link_util: 
    #         link_util[dict['time']] = list()

    #     link_util[dict['time']].append(float(dict['bw']))
    # value = link_util.values()
    # time_index = [i for i in range(0, len(value)) if i % freq == 0]

    # for i in time_index:
    #     aggr_dict[str(i)] = list()
    #     aggr_dict[str(i)].extend(list(value)[i])
    
    for l in data: 
        if l['round'] not in link_util: 
            link_util[l['round']] = list()
        link_util[l['round']].append(float(l['bw']))
    value = link_util.values()

    time_index = [i for i in range(len(value)) if i % (freq/2) == 0]
    for i in time_index:
        aggr_dict[str(2*i)] = list()
        aggr_dict[str(2*i)].extend(list(value)[i])

    # time_index = [i for i in range(len(value)) if i % freq == 0]
    # for i in time_index:
    #     aggr_dict[str(i)] = list()
    #     aggr_dict[str(i)].extend(list(value)[i])

    return aggr_dict

def _select_all(data):
    url = "http://localhost:5000/mydb/" + data
    response = requests.get(url)
    return response
    

if __name__ == "__main__":
    get_data()
