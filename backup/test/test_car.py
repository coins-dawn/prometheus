import requests
import json


url = "http://localhost:3000/route/car"
headers = {"Content-Type": "application/json"}


def test_route_car():
    payload = {
        "stops": [
            {"coord": {"lat": 36.61095, "lon": 137.2509}, "name": "stop1"},
            {"coord": {"lat": 36.61065, "lon": 137.2145}, "name": "stop2"},
            {"coord": {"lat": 36.61303, "lon": 137.1858}, "name": "stop3"},
            {"coord": {"lat": 36.63100, "lon": 137.2149}, "name": "stop4"},
        ],
        "start_time_list": ["10:00", "11:00", "13:00"],
        "debug": False,
    }

    # route全体
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "OK"
    route_info = response_data["result"]["route_info"]
    assert route_info["distance"] == 15247.87
    assert route_info["duration"] == 1091.0

    # subroute 0
    subroute_0 = route_info["subroutes"][0]
    assert subroute_0["duration"] == 212.0
    assert subroute_0["distance"] == 3433.62
    assert (
        subroute_0["polyline"]
        == "msm~EkxudY@BnA~LHz@`@zDRvARnA^zB?r@CdCKxEEpBAd@Ej@In@ABOl@Qd@]p@q@vA[bAYjBq@rESv@]v@Yn@Uj@SxAGdBExAShFUhEIjBMnBYjCi@xD_@vCCZF`@JTLPhAdALL`@ZrAfAh@j@^b@\\b@DFbB~BLNJFEtA_@hPObH?TAdAMxFItGB|AHdB`@hNN`GAhE?j@EhA"
    )
    assert subroute_0["org"]["name"] == "stop1"
    assert subroute_0["dst"]["name"] == "stop2"

    # subroute 1
    subroute_1 = route_info["subroutes"][1]
    assert subroute_1["duration"] == 201.0
    assert subroute_1["distance"] == 2584.59
    assert (
        subroute_1["polyline"]
        == "upm~EwundYEnAKrCOjCCdDAvHEbGEpG[rFa@rIYfEaArNcApLU`B}@zKk@vGMzC?N@bDPdFArAMzAC^Eb@I`AWrE?HQtDElAKtFMvF"
    )
    assert subroute_1["org"]["name"] == "stop2"
    assert subroute_1["dst"]["name"] == "stop3"

    # subroute 2
    subroute_2 = route_info["subroutes"][2]
    assert subroute_2["duration"] == 361.0
    assert subroute_2["distance"] == 4591.89
    assert (
        subroute_2["polyline"]
        == "o`n~EkbidYLwFJuFDmAPuD?IVsEHaADc@B_@L{AeBJkC@eC?wFAk@C[E]IYI[MYMwEqCOI[M_@GUEYA]A_A@qBBcFFU@{B?m@Ay@EaCQQA[Cc@Ei@EiCSa@CyJ{@y@GQCwDYy@GaCQaEk@mAQEAoF}@s@M{@EcAAoBLUD?]?oC?aC?sB@qDBeAHqAb@yFHcADe@Dc@b@eGL}APwBJuAFuB?}AEaECmCKaKGgFAY?]A[AsAE}EBwCDwAJqBLiALyAT{BLkAVqB"
    )
    assert subroute_2["org"]["name"] == "stop3"
    assert subroute_2["dst"]["name"] == "stop4"

    # subroute 3
    subroute_2 = route_info["subroutes"][3]
    assert subroute_2["duration"] == 317.0
    assert subroute_2["distance"] == 4637.77
    assert (
        subroute_2["polyline"]
        == "ipq~EsxndYHq@^cDJcAV}BF{@@aACgAKeBE}@I_BMsB|@OpAKXAV?dAIbCQ^EjD]p@K`AOvAYpDq@v@OrAYxFiAhE{@hEcAD?hCw@\\IpA[|Ac@zBe@l@[n@o@vAmA|ByBp@g@rGcG`@_@f@e@f@iA~@oBJUnCqFPg@Nc@TqAx@qENa@Zy@`@i@d@o@HA`@I|@CVAJAB[^wCh@yDXkCLoBHkBTiERiFDyAFeBRyATk@Xo@\\w@Rw@p@sEXkBZcAp@wA\\q@Pe@Nm@@CHo@Dk@@e@DqBJyEBeC?s@_@{BSoASwAa@{DI{@oA_MAC"
    )
    assert subroute_2["org"]["name"] == "stop4"
    assert subroute_2["dst"]["name"] == "stop1"

    # 時刻表
    time_table = response_data["result"]["time_table"]
    assert len(time_table) == len(payload["stops"])
    assert time_table[0]["stop_name"] == "stop1"
    assert time_table[0]["time_list"] == ["10:00", "11:00", "13:00"]
    assert time_table[1]["stop_name"] == "stop2"
    assert time_table[1]["time_list"] == ["10:03", "11:03", "13:03"]
    assert time_table[2]["stop_name"] == "stop3"
    assert time_table[2]["time_list"] == ["10:06", "11:06", "13:06"]
    assert time_table[3]["stop_name"] == "stop4"
    assert time_table[3]["time_list"] == ["10:12", "11:12", "13:12"]
