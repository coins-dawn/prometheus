#!/bin/bash

docker run -it --rm -p 8000:8080 \
    -e JAVA_TOOL_OPTIONS='-Xmx8g' \
    -v "$(pwd)/network:/var/opentripplanner" \
    docker.io/opentripplanner/opentripplanner:2.7.0_2024-11-26T16-34 --load --serve
