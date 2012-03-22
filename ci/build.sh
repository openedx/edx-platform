#! /bin/bash

set -x
set -e

#sass sass:static/css -r templates/sass/bourbon/lib/bourbon.rb --style :compressed

if [ -z "${GIT_COMMIT}" ]; then
    GIT_COMMIT=$(git rev-parse HEAD)
fi

if [ -z "${GIT_BRANCH}" ]; then
    GIT_BRANCH=$(git symbolic-ref -q HEAD)
    GIT_BRANCH=${GIT_BRANCH##refs/heads/}
    GIT_BRANCH=${GIT_BRANCH:-HEAD}
fi
GIT_BRANCH=${GIT_BRANCH##origin/}
GIT_BRANCH=${GIT_BRANCH//\//_}

if [ -z "${BUILD_NUMBER}" ]; then
    BUILD_NUMBER=dev
fi

REPO_ROOT=$(dirname $(pwd)/$(dirname $0))
BUILD_DIR=${REPO_ROOT}/build

if [ "${GIT_BRANCH}" == "master" ]; then
    NAME=mitx
else
    NAME=mitx-${GIT_BRANCH}
fi

mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
fpm -s dir -t deb \
    --exclude=build \
    --exclude=ci \
    --exclude=.git \
    --prefix=/opt/wwc/mitx \
    --name ${NAME} \
    --version 0.1 \
    --iteration ${BUILD_NUMBER}-${GIT_COMMIT} \
    -a all \
    ${REPO_ROOT}
