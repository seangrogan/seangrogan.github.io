#!/bin/sh
# Docker health check for the newsfeed container (see scripts/compose.yaml).
# Healthy if the last fully successful check finished within two intervals
# (plus half an hour of slack).
last=/tmp/newsfeed_last_ok
[ -f "$last" ] || exit 1
age=$(( $(date +%s) - $(cat "$last") ))
limit=$(( ${INTERVAL_HOURS:-6} * 3600 * 2 + 1800 ))
[ "$age" -lt "$limit" ]
