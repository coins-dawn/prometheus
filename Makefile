# otpで利用するネットワークの元データをダウンロード
.PHONY: download-data
download-data:
	./script/download_data.sh

# otpで利用するネットワークをコンバート
.PHONY: convert-network
convert-network:
	./script/convert.sh

# localhost:8000でotpサーバを起動
.PHONY: run-otp-server
run-otp-server:
	./script/run_otp_sever.sh

# localhost:3000でprometheusサーバを起動
.PHONY: up
up:
	docker compose up -d

# prometheusサーバを終了
.PHONY: down
down:
	docker compose down

# pythonコードをフォーマットする
# note:ホスト側にblackがインストールされている必要あり
.PHONY: format
format:
	black .

# prometheusのテストを実行する
# hote:ホスト側にpytestがインストールされている必要あり
.PHONY: test
test:
	pytest . -s
