# prometheus

コミュニティバスの経路シミュレートサービスです。

![prometheus](prometheus.png)

### 前提条件
* python, pip がインストールされている

### 使い方
```
# 依存モジュールをインストール
make fetch

# 127.0.0.1:8000でprometheusを起動
make run-server

# サンプルリクエストを投げる
# => リポジトリトップにroute.kmlが出力される
make sample-request
```