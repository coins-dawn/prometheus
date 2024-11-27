# prometheus

コミュニティバスの経路をシミュレートするサービスのバックエンドリポジトリです。

### 利用方法
```
# OSMとGTFSをダウンロード
make download-data

# otpサーバで利用するネットワークデータを作成
make convert-network

# localhost:8080でotpサーバを起動
make run-otp-server
```