import requests
import pprint

# OTP サーバのエンドポイント
OTP_GRAPHQL_URL = "http://localhost:8080/otp/routers/default/index/graphql"

# GraphQL クエリ: 複数のルートを取得するクエリ
query = """
query {
  route1: plan(
    from: {
      lat: 34.17984991363257, 
      lon: 134.6182768573242
    }, 
    to: {
      lat: 34.17563182715784, 
      lon: 134.60562299824946
    },
    transportModes: [{mode: CAR}]
  ) 
  {
    itineraries {
      duration
      legs {
        mode
        from { name }
        to { name }
        distance
        legGeometry { points }
      }
    }
  }
  route2: plan(
    from: {
      lat: 34.19119935381726, 
      lon: 134.5950549397854
    }, 
    to: {
      lat: 34.179897662352815, 
      lon: 134.60117496019149
    }, 
    transportModes: [{mode: CAR}]
  ) {
    itineraries {
      duration
      legs {
        mode
        from { name }
        to { name }
        distance
        legGeometry { points }
      }
    }
  }
}
"""

# GraphQL リクエストの送信
response = requests.post(OTP_GRAPHQL_URL, json={"query": query})

# 結果の確認
if response.status_code == 200:
    data = response.json()
    pprint.pprint(data)
    # for route, result in data["data"].items():
    #     print(f"{route} results:")
    #     for itinerary in result["itineraries"]:
    #         print(f"  Duration: {itinerary['duration']} seconds")
    #         for leg in itinerary["legs"]:
    #             print(f"    Mode: {leg['mode']}")
    #             print(f"    From: {leg['from']['name']} to {leg['to']['name']}")
    #             print(f"    Distance: {leg['distance']} meters")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
