# prometheus

![prometheus](prometheus.jpg)

コミュニティバスの経路をシミュレートするサービスのバックエンドリポジトリです。

### 利用方法
```
# OSMとGTFSをダウンロード
make download-data

# otpサーバで利用するネットワークデータを作成
make convert-network

# 8080ポートでotpサーバを起動
# 3000ポートでprometheusサーバを起動
make up

# サービスを終了
make down
```