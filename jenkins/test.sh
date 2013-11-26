#! /bin/bash

set -e
set -x

##
## requires >= 1.3.0 of the Jenkins git plugin
##

function github_status {
    if [[ ! ${GIT_URL} =~ git@github.com:([^/]+)/([^\.]+).git ]]; then
        echo "Cannot parse Github org or repo from URL, using defaults."
        ORG="edx"
        REPO="edx-platform"
    else
        ORG=${BASH_REMATCH[1]}
        REPO=${BASH_REMATCH[2]}
    fi

    gcli status create $ORG $REPO $GIT_COMMIT \
         --params=$1 \
                  target_url:$BUILD_URL \
                  description:"Build #$BUILD_NUMBER $2" \
         -f csv
}

function github_mark_failed_on_exit {
    trap '[ $? == "0" ] || github_status state:failure "failed"' EXIT
}

git remote prune origin

github_mark_failed_on_exit
github_status state:pending "is running"

# Reset the submodule, in case it changed
git submodule foreach 'git reset --hard HEAD'

# Assumes that Xvfb has been started by upstart
# and is capturing display :1
# The command for this is:
# /usr/bin/Xvfb :1 -screen 0 1024x268x24
# This allows us to run Chrome or Firefox without a display
export DISPLAY=:1

# Set the IO encoding to UTF-8 so that askbot will start
export PYTHONIOENCODING=UTF-8

GIT_BRANCH=${GIT_BRANCH/HEAD/master}

# When running in parallel on jenkins, workspace could be suffixed by @x
# In that case, we want to use a separate virtualenv that matches up with
# workspace
#
# We need to handle both the case of /path/to/workspace
# and /path/to/workspace@2, which is why we use the following substitutions
#
# $WORKSPACE is the absolute path for the workspace
WORKSPACE_SUFFIX=$(expr "$WORKSPACE" : '.*\(@.*\)') || true

VIRTUALENV_DIR="/mnt/virtualenvs/${JOB_NAME}${WORKSPACE_SUFFIX}"

if [ ! -d "$VIRTUALENV_DIR" ]; then
    mkdir -p "$VIRTUALENV_DIR"
    virtualenv --system-site-packages "$VIRTUALENV_DIR"
fi

export PIP_DOWNLOAD_CACHE=/mnt/pip-cache

source $VIRTUALENV_DIR/bin/activate

bundle install

rake install_prereqs
rake clobber

# Run the unit tests (use phantomjs for javascript unit tests)
rake test

# Generate pylint and pep8 reports
rake pep8 > pep8.log || cat pep8.log
rake pylint > pylint.log || cat pylint.log

# Generate coverage reports
rake coverage

# Generate quality reports
rake quality

rake autodeploy_properties

github_status state:success "passed"
