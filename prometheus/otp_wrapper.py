from request import CarRequest
from response import CarResponse


def search_car_route(car_request: CarRequest) -> CarResponse:
    response = CarResponse(
        **{
            "duration": 1.0,
            "distance": 2.0,
            "subroutes": [
                {
                    "org": {
                        "coord": {"lat": 34.15646, "lon": 134.6144},
                        "name": "orgname",
                    },
                    "dst": {
                        "coord": {"lat": 34.16423, "lon": 134.6277},
                        "name": "dstname",
                    },
                    "duration": 3.0,
                    "distance": 2.0,
                    "polyline": "polyline",
                }
            ],
        }
    )

    return response
