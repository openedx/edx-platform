#sass sass:static/css -r templates/sass/bourbon/lib/bourbon.rb --style :compressed

if [ -z "${GIT_COMMIT}" ]; then
    GIT_COMMIT=$(git rev-parse HEAD)
fi

if [ -z "${GIT_BRANCH}" ]; then
    GIT_BRANCH=$(git symbolic-ref -q HEAD)
    GIT_BRANCH=${GIT_BRANCH##refs/heads/}
    GIT_BRANCH=${GIT_BRANCH:-HEAD}
fi

if [ -z "${BUILD_NUMBER}" ]; then
    BUILD_NUMBER=dev
fi

ID=mitx-${GIT_BRANCH}-${BUILD_NUMBER}-${GIT_COMMIT}
tar --exclude=.git --exclude=build -czf build/${ID}.tgz ${REPO}
