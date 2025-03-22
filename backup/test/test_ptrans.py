import requests
import json

url = "http://localhost:3000/route/ptrans"
headers = {"Content-Type": "application/json"}


def test_route_ptrans():
    payload = {
        "org_coord": {"lat": 36.69656, "lon": 137.1366},
        "dst_coord": {"lat": 36.68804, "lon": 137.2109},
        "start_time": "2024-12-25 10:00:00",
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "OK"
    result = response_data["result"]

    assert result["duration"] == 3302.0
    assert result["start_time"] == "2024-12-25 10:24:16"
    assert result["goal_time"] == "2024-12-25 11:19:18"

    subroutes = result["subroutes"]
    assert len(subroutes) == 3

    # subroute 0
    subroute_0 = subroutes[0]
    assert subroute_0["mode"] == "WALK"
    assert subroute_0["start_time"] == "2024-12-25 10:24:16"
    assert subroute_0["goal_time"] == "2024-12-25 10:42:00"
    assert subroute_0["distance"] == 1277.68
    assert subroute_0["duration"] == 1064.0
    assert (
        subroute_0["polyline"]
        == "ih~~Eun_dY?XtGqD~I}E~AqIn@yDBQ?G@KDMBIDWFq@Fc@Lk@PsACOEGBQ@EBSJGDKx@iG?EBIHETGJGDUd@uDBMHIFA@EBKKS?MTsAEIDUDOj@uBTi@EC"
    )

    # subroute 1
    subroute_1 = subroutes[1]
    assert subroute_1["mode"] == "BUS"
    assert subroute_1["start_time"] == "2024-12-25 10:42:00"
    assert subroute_1["goal_time"] == "2024-12-25 11:10:00"
    assert subroute_1["distance"] == 10247.64
    assert subroute_1["duration"] == 1680.0
    assert (
        subroute_1["polyline"]
        == "me}~EmradYcBfIrHbDtEnA????zAn@dDfCrEt@??lYN|AfDfCzCrAjAL~B????AtBGd@v@fA|FCxBmBp@[tDj@??l@_Bo@gGGyEaAqL`BwD??b@{AbD~DpMiYcEkF??mOeO????ySeR????_LwK??qu@{r@????gJ{O????_Scc@????cGuR??oEwUAmG??o@gDaO}UxGaH??xMmM????xOiT??~D_MrCcPdFi]??jAe\\"
    )
    bus_info = subroute_1["bus_info"]
    assert bus_info["agency"] == "富山地方鉄道株式会社"
    assert bus_info["org_stop_name"] == "ファミリーパーク前"
    assert bus_info["dst_stop_name"] == "丸の内"
    assert bus_info["line_name"] == "富大附病院・朝日循環線"

    # subroute 2
    subroute_2 = subroutes[2]
    assert subroute_2["mode"] == "WALK"
    assert subroute_2["start_time"] == "2024-12-25 11:10:00"
    assert subroute_2["goal_time"] == "2024-12-25 11:19:18"
    assert subroute_2["distance"] == 607.97
    assert subroute_2["duration"] == 558.0
    assert (
        subroute_2["polyline"]
        == "wl}~EowmdYA?\\sHJ?B?J@DEFCtAMNAJAHAt@I|@@pCR?Kp@DnAHPEJM??XCrCPIjA"
    )
