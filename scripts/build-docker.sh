#!/bin/sh
# Utility script 
# Call from the repository root: ./scripts/build-docker.sh

# Build image
docker build -t ulikoehler/flaredns:latest -t ulikoehler/flaredns:1 -t ulikoehler/flaredns:1.1 .
# Push image
docker push ulikoehler/flaredns:latest
docker push ulikoehler/flaredns:1
docker push ulikoehler/flaredns:1.1