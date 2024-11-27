#!/bin/bash

DSTDIR=network/input

mkdir -p $DSTDIR

# OSM
curl -L  https://download.geofabrik.de/asia/japan/shikoku-latest.osm.pbf -o $DSTDIR/shikoku-latest.osm.pbf

# GTFS
# 鳴門市地域バス
curl -L https://api.gtfs-data.jp/v2/organizations/narutocity/feeds/narutocitychiikibus/files/feed.zip?rid=current -o $DSTDIR/tokushima-local-bus-gtfs.zip
