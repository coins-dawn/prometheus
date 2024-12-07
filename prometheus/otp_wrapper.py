import requests
from request import CarRequest
from response import CarResponse, CarSubRoute
from utility import generate_random_string

OTP_GRAPHQL_URL = "http://localhost:8000/otp/routers/default/index/graphql"


def search_car_route(car_request: CarRequest) -> CarResponse:
    dst_stops = car_request.stops[1:] + [car_request.stops[0]]
    query_str = "query {"
    for i, (org_stop, dst_stop) in enumerate(zip(car_request.stops, dst_stops)):
        query_str += f"""
        route{i}: plan(
            from: {{
                lat: {org_stop.coord.lat},
                lon: {org_stop.coord.lon}
            }},
            to: {{
                lat: {dst_stop.coord.lat},
                lon: {dst_stop.coord.lon}
            }},
            transportModes: [{{mode: CAR}}]
        )
        {{
            itineraries {{
                legs {{
                    distance
                    duration
                    legGeometry {{ points }}
                }}
            }}
        }}
        """
    query_str += "}"

    otp_response = requests.post(OTP_GRAPHQL_URL, json={"query": query_str})

    if otp_response.status_code != 200:
        raise Exception("otpサーバへの通信に失敗しました。")

    result = otp_response.json()

    subroutes: list[CarSubRoute] = []
    for i, route_name in enumerate(result["data"]):
        route = result["data"][route_name]
        distance = route["itineraries"][0]["legs"][0]["distance"]
        duration = route["itineraries"][0]["legs"][0]["duration"]
        polyline = route["itineraries"][0]["legs"][0]["legGeometry"]["points"]
        org_stop = car_request.stops[i]
        dst_stop = (
            car_request.stops[i + 1]
            if i < len(car_request.stops) - 1
            else car_request.stops[0]
        )
        subroutes.append(
            CarSubRoute(
                org=org_stop,
                dst=dst_stop,
                duration=duration,
                distance=distance,
                polyline=polyline,
            )
        )

    route_id = generate_random_string()
    duration = sum(subroute.duration for subroute in subroutes)
    distance = sum(subroute.distance for subroute in subroutes)
    response = CarResponse(
        route_id=route_id, duration=duration, distance=distance, subroutes=subroutes
    )

    return response
