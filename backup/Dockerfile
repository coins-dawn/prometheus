FROM python:3.11-slim

WORKDIR /prometheus

COPY prometheus/ /prometheus/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "app:app"]
