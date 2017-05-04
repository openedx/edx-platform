#!/bin/bash

set -x
set -e
mkdir -p .docker/wheelhouse .docker/node_modules

docker build -t edxapp-builder - < build.docker
docker run --rm -v "$(pwd)"/requirements:/requirements -v "$(pwd)"/.docker/wheelhouse:/wheelhouse -v $(pwd)/package.json:/package.json -v "$(pwd)"/.docker/node_modules:/node_modules edxapp-builder
docker build . -t edxops/edxapp:devstack
