from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "OK"

if __name__ == '__main__':
    # Render上でポート番号は環境変数 PORT で指定される場合もありますが、
    # ここでは簡略化のため固定のポート番号を使用しています。
    app.run(host='0.0.0.0', port=5000)
