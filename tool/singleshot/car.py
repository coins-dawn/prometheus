import json
import sys
from prometheus.car.car_searcher import CarSearcher
from prometheus.car.car_input import CarSearchInput


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python car.py <input_json_path>")
        sys.exit(1)
    json_path = sys.argv[1]
    searcher = CarSearcher()
    with open(json_path, encoding="utf-8") as f:
        input_str = f.read()
    search_input = CarSearchInput(**json.loads(input_str))
    result = searcher.search(search_input)
    print(result)
