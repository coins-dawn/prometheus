.PHONY: convert
convert:
	python create_network.py

.PHONY: search
search:
	python search.py

.PHONY: run-server
run-server:
	python app.py
