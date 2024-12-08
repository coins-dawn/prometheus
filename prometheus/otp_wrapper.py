import requests
from datetime import time
from request import CarRequest, PtransRequest
from response import (
    CarResponse,
    CarSubRoute,
    RouteInfo,
    TimeTable,
    TimeTableElement,
    PtransResponse,
)
from utility import generate_random_string, add_times, add_seconds_to_time

OTP_GRAPHQL_URL = "http://otp:8080/otp/routers/default/index/graphql"


def create_route_info(car_request: CarRequest, result: dict) -> RouteInfo:
    """open trip plannerの返却値を元にルート情報を作成する。"""
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
    duration = sum(subroute.duration for subroute in subroutes)
    distance = sum(subroute.distance for subroute in subroutes)
    return RouteInfo(duration=duration, distance=distance, subroutes=subroutes)


def create_time_table(car_request: CarRequest, route_info: RouteInfo) -> TimeTable:
    """経路情報を元に時刻表を作成する。"""
    time_table_element_list: list[TimeTableElement] = []
    for stop in car_request.stops:
        time_table_element_list.append(
            TimeTableElement(stop_name=stop.name, time_list=[])
        )

    for start_time in car_request.start_time_list:
        current_duration_sum: time = time(0, 0, 0)
        for subroute, time_table_element in zip(
            route_info.subroutes, time_table_element_list
        ):
            stop = subroute.org
            assert stop.name == time_table_element.stop_name
            time_table_element.time_list.append(
                add_times(current_duration_sum, start_time)
            )
            current_duration_sum = add_seconds_to_time(
                current_duration_sum, int(subroute.duration)
            )
    return TimeTable(time_table_elements=time_table_element_list)


def search_car_route(car_request: CarRequest) -> CarResponse:
    """open trip plannerで車経路探索（経由地あり）を実行する。"""
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
    route_id = generate_random_string()
    route_info = create_route_info(car_request, result)
    time_table = create_time_table(car_request, route_info)
    response = CarResponse(
        route_id=route_id, route_info=route_info, time_table=time_table
    )

    return response


def search_ptrans_route(ptrans_request: PtransRequest) -> PtransResponse:
    response = PtransResponse()
    return response
