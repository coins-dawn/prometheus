#!/bin/bash

docker run --rm \
    -e JAVA_TOOL_OPTIONS='-Xmx8g' \
    -v "$(pwd)/network/input:/var/opentripplanner" \
    docker.io/opentripplanner/opentripplanner:2.7.0_2024-11-26T16-34 --build --save

mv $(pwd)/network/input/graph.obj network
