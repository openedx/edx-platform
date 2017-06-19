#!/usr/bin/env bash

set -e

# Return status is that of the last command to fail in a
# piped command, or a zero if they all succeed.
set -o pipefail

# does list contain value
# usage: 
# - contains "10 11 12" "12": 0
# - contains "10 11 12" "13": 1
contains() {
    [[ $1 =~ (^|[[:space:]])$2($|[[:space:]]) ]] && exit 0 || exit 1
}

# start chrome
if [ contains "lms-acceptance cms-acceptance" "$TEST_SUITE" ]; then
    google-chrome-stable --headless --disable-gpu --remote-debugging-port=8003 http://localhost
    sleep 3
fi

# start svfb display for firefox usage
if [ contains "js-unit lms-acceptance cms-acceptance commonlib-js-unit" "$TEST_SUITE" ]; then
    export DISPLAY=:99.0
    sh -e /etc/init.d/xvfb start
    sleep 3
fi
