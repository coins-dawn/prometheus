.PHONY: fetch
fetch:
	pip install -r requirements.txt

.PHONY: format
format:
	black prometheus

.PHONY: run-server
run-server:
	PYTHONPATH=. python -m prometheus.app

.PHONY: sample-request
sample-request:
	curl -X POST http://localhost:8000/search/car \
	-H "Content-Type: application/json" \
	-d @sample/input.json

.PHONY: car-singleshot
car-singleshot:
	PYTHONPATH=$$PYTHONPATH:./prometheus python prometheus/car_searcher.py

.PHONY: ptrans-singleshot
ptrans-singleshot:
	PYTHONPATH=$$PYTHONPATH:./prometheus python prometheus/ptrans_searcher.py
