.PHONY: fetch
fetch:
	pip install -r requirements.txt

.PHONY: format
format:
	black prometheus test

.PHONY: run-server
run-server:
	PYTHONPATH=. python -m prometheus.app

# データを作成する
.PHONY: best-combus-stop-sequences
best-combus-stop-sequences:
	python tool/best_combus_stop_sequences.py \
		data/archive/combus_stops.json \
		data/archive/combus_routes.json \
		data/archive/spot_list.json \
		data/static/best_combus_stop_sequences.json \
		data/static/request_response.bin
