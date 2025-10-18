.PHONY: fetch
fetch:
	pip install -r requirements.txt

.PHONY: format
format:
	black prometheus test

.PHONY: run-server
run-server:
	PYTHONPATH=. python -m prometheus.app

