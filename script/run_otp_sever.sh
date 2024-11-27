#!/bin/bash

docker run -it --rm -p 8080:8080 \
    -e JAVA_TOOL_OPTIONS='-Xmx8g' \
    -v "$(pwd)/network:/var/opentripplanner" \
    docker.io/opentripplanner/opentripplanner:latest --load --serve
