.PHONY: fetch
fetch:
	pip install -r requirements.txt

.PHONY: format
format:
	black prometheus test

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
	PYTHONPATH=$$PYTHONPATH:./prometheus python tool/singleshot/car.py tool/singleshot/car_input.json

.PHONY: ptrans-singleshot
ptrans-singleshot:
	PYTHONPATH=$$PYTHONPATH:./prometheus python tool/singleshot/ptrans.py tool/singleshot/ptrans_input.json

.PHONY: test
test:
	PYTHONPATH=$$PYTHONPATH:./prometheus pytest -s test
