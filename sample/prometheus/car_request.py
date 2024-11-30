import requests
import json

url = "http://localhost:3000/route/car"

payload = {
    "key": "value",
    "example": 12345
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print("Status Code:", response.status_code)
print("Response JSON:", response.json())