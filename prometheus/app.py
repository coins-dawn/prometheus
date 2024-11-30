from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def ping():
    return "OK"

@app.route("/route/car", methods=["POST"])
def search_car():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    response_data = {
        "received": data,
        "message": "POST request processed successfully"
    }
    
    return jsonify(response_data), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
