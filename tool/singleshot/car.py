import json
from prometheus.car.car_searcher import CarSearcher
from prometheus.car.car_input import CarSearchInput


if __name__ == "__main__":
    searcher = CarSearcher()
    input_str = """
{
    "route-name": "循環バス",
    "start-time": "10:00",
    "stops": [
        {
            "name": "バス停1",
            "coord": {
                "lat": 36.65742,
                "lon": 137.17421
            }
        },
        {
            "name": "バス停2",
            "coord": {
                "lat": 36.68936,
                "lon": 137.18519
            }
        },
        {
            "name": "バス停3",
            "coord": {
                "lat": 36.67738,
                "lon": 137.23892
            }
        },
        {
            "name": "バス停4",
            "coord": {
                "lat": 36.65493,
                "lon": 137.24001
            }
        },
        {
            "name": "バス停5",
            "coord": {
                "lat": 36.63964,
                "lon": 137.21958
            }
        }
    ]
}
"""
    search_input = CarSearchInput(**json.loads(input_str))
    result = searcher.search(search_input)
    print(result)
