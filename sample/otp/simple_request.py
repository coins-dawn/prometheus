import requests

# OTP サーバのエンドポイント
OTP_GRAPHQL_URL = "http://localhost:8080/otp/routers/default/index/graphql"

# GraphQL クエリ: 指定した出発地と目的地のルートを取得
query = """
query ($from: InputCoordinates!, $to: InputCoordinates!) {
  plan(from: $from, to: $to) {
    itineraries {
      duration
      legs {
        mode
        startTime
        endTime
        from {
          name
        }
        to {
          name
        }
        distance
      }
    }
  }
}
"""

# 変数: 出発地と目的地の座標
variables = {
    "from": {"lat": 34.171138395609134, "lon": 134.5999975839498},
    "to": {"lat": 34.1703296176689, "lon": 134.63137558440366},
}

# GraphQL リクエストの送信
response = requests.post(OTP_GRAPHQL_URL, json={"query": query, "variables": variables})

# 結果の確認
if response.status_code == 200:
    data = response.json()
    print("Routes found:")
    for itinerary in data["data"]["plan"]["itineraries"]:
        print(f"Duration: {itinerary['duration']} seconds")
        for leg in itinerary["legs"]:
            print(f"  Mode: {leg['mode']}")
            print(f"  From: {leg['from']['name']} to {leg['to']['name']}")
            print(f"  Distance: {leg['distance']} meters")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
