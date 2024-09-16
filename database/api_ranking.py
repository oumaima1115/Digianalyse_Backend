import requests

def get_ranking(keyword):
    url = "https://google-keyword-insight1.p.rapidapi.com/keysuggest/"

    querystring = {"keyword":keyword,"location":"US","lang":"en"}

    headers = {
        "x-rapidapi-key": "8e9dd20399msh09e9ced25a3fda9p157ea5jsn84c0bfbd8926",
        "x-rapidapi-host": "google-keyword-insight1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    print(keyword)
    return data