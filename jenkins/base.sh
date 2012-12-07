#! /bin/bash

function github_status {
    gcli status create mitx mitx $GIT_COMMIT \
         --params=$1 \
                  target_url:$BUILD_URL \
                  description:"Build #$BUILD_NUMBER $2" \
         -f csv
}

function github_mark_failed_on_exit {
    trap '[ $? == "0" ] || github_status state:failed "failed"' EXIT
}