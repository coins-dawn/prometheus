import json

STATIC_AREA_SEARCH_REQUEST_PATH = "data/static/area_search_request.json"
STATIC_AREA_SEARCH_RESPONSE_PATH = "data/static/area_search_response.json"

def load_static_area_search_request():
    with open(STATIC_AREA_SEARCH_REQUEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    
def is_valid_request(body: dict) -> bool:
    static_request = load_static_area_search_request()
    return body == static_request


def load_static_area_search_response():
    with open(STATIC_AREA_SEARCH_RESPONSE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
