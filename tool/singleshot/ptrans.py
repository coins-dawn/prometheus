import json
import sys
from prometheus.ptrans.ptrans_searcher import PtransSearcher
from prometheus.ptrans.ptrans_input import PtransSearchInput
from prometheus.ptrans.ptrans_visualizer import generate_ptrans_route_kml

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ptrans.py <input_json_path>")
        sys.exit(1)
    json_path = sys.argv[1]
    ptrans_searcher = PtransSearcher()
    with open(json_path, encoding="utf-8") as f:
        input_str = f.read()
    search_input = PtransSearchInput(**json.loads(input_str))
    result = ptrans_searcher.search(search_input)
    print(result)
    generate_ptrans_route_kml(
        node_sequence=result[0],
        stops_dict=ptrans_searcher.stops,
        shape_dict=ptrans_searcher.shape_dict,
        start_coord=(search_input.start.lat, search_input.start.lon),
        goal_coord=(search_input.goal.lat, search_input.goal.lon),
        output_path="ptrans_result.kml",
    )
