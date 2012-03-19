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

ID=mitx-${GIT_BRANCH}-${BUILD_NUMBER}-${GIT_COMMIT}
REPO_ROOT=$(dirname $0)/..
BUILD_DIR=${REPO_ROOT}/build

mkdir -p ${BUILD_DIR}
tar -v --exclude=.git --exclude=build --transform="s#^#mitx/#" -czf ${BUILD_DIR}/${ID}.tgz ${REPO_ROOT}
