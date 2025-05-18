import requests

if __name__ == "__main__":
    url = "http://localhost:3003/"
    response = requests.get(url)
    print(response.text)