# otpで利用するネットワークの元データをダウンロード
.PHONY: download-data
download-data:
	./script/download_data.sh

# otpで利用するネットワークをコンバート
.PHONY: convert-network
convert-network:
	./script/convert.sh

# 8080ポートでoptサーバを起動
# 3000ポートでprometheusサーバを起動
.PHONY: up
up:
	docker compose up -d --build

# サービスを終了する
.PHONY: down
down:
	docker compose down

# prometheusサーバのrouteキャッシュを削除する
.PHONY: clear-route-cache
clear-route-cache:
	rm prometheus/routes/*

# pythonコードをフォーマットする
# note:ホストにblackがインストールされている必要あり
.PHONY: format
format:
	black .

# prometheusのテストを実行する
# note:ホストにpytestがインストールされている必要あり
.PHONY: test
test:
	pytest . -s
