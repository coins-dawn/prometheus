#!/bin/bash

docker run --rm \
    -e JAVA_TOOL_OPTIONS='-Xmx8g' \
    -v "$(pwd)/network/input:/var/opentripplanner" \
    docker.io/opentripplanner/opentripplanner:latest --build --save

mv $(pwd)/network/input/graph.obj network
