.PHONY: format
format:
	black prometheus

.PHONY: run-server
run-server:
	PYTHONPATH=. python -m prometheus.app

.PHONY: sample-request
sample-request:
	curl -X POST http://localhost:8000/route \
	-H "Content-Type: application/json" \
	-d @sample/input.json --output route.kml
