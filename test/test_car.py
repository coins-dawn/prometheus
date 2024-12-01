import requests
import json


url = "http://localhost:3000/route/car"
headers = {"Content-Type": "application/json"}


def test_standard():
    payload = {
        "stops": [
            {
                "coord": {"lat": 34.15646, "lon": 134.6144},
                "name": "stop1",
            },
            {"coord": {"lat": 34.16906, "lon": 134.6155}, "name": "stop2"},
            {
                "coord": {"lat": 34.16423, "lon": 134.6277},
                "name": "stop3",
            },
        ],
    }

    # 全体
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "OK"
    result = response_data["result"]
    assert result["distance"] == 4903.0
    assert result["duration"] == 547.0

    # subroute 0
    subroute_0 = result["subroutes"][0]
    assert subroute_0["duration"] == 187.0
    assert subroute_0["distance"] == 1721.72
    assert (
        subroute_0["polyline"]
        == "abnoE}~rtXa@c@s@k@gA}@iAtAyBjDm@z@wBfDeCnDIB[Mu@a@UKgGiB_@G_EQa@G_AvDg@UKE}BaAuD_BwGyCCAYMIEcAa@o@Sy@Qw@IkECO?m@Aw@AY?"
    )
    assert subroute_0["org"]["name"] == "stop1"
    assert subroute_0["dst"]["name"] == "stop2"

    # subroute 1
    subroute_1 = result["subroutes"][1]
    assert subroute_1["duration"] == 186.0
    assert subroute_1["distance"] == 1494.84
    assert (
        subroute_1["polyline"]
        == "uspoEi}rtX}CCDmJBoAF{@Fm@He@Ja@Ja@\\}@`@y@nBgDZk@pAwBfB{ClAsBZg@xDwGn@eAjCyEm@c@a@[c@[DKrBaDnAuBp@aAJKUU"
    )
    assert subroute_1["org"]["name"] == "stop2"
    assert subroute_1["dst"]["name"] == "stop3"

    # subroute 2
    subroute_2 = result["subroutes"][2]
    assert subroute_2["duration"] == 174.0
    assert subroute_2["distance"] == 1686.44
    assert (
        subroute_2["polyline"]
        == "swooEwjutXTTKJq@`AoAtBsB`DEJb@Z`@Zl@b@XTVRjBhCxAhBnA~A|AlBh@p@PTP\\b@hABFl@rAr@hAzArBlAxAxA|Ah@`@vApAzBfBr@n@xAfAbCjBVPzCzBjAjAfA|@r@j@`@b@"
    )
    assert subroute_2["org"]["name"] == "stop3"
    assert subroute_2["dst"]["name"] == "stop1"
