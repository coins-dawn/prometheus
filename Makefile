.PHONY: format
format:
	black prometheus

.PHONY: run-server
run-server:
	python prometheus/app.py

.PHONY: sample-request
sample-request:
	curl -X POST http://localhost:8000/route \
	-H "Content-Type: application/json" \
	-d @sample/input.json --output route.kml
