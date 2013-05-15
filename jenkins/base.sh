##
## requires >= 1.3.0 of the Jenkins git plugin
##

function github_status {

    if [[ ! ${GIT_URL} =~ git@github.com:([^/]+)/([^\.]+).git ]]; then
        echo "Cannot parse Github org or repo from URL, using defaults."
        ORG="edx"
        REPO="mitx"
    else
        ORG=${BASH_REMATCH[1]}
        REPO=${BASH_REMATCH[2]}
    fi

    gcli status create $ORG $REPO $GIT_COMMIT \
         --params=$1 \
                  target_url:$BUILD_URL \
                  description:"Build #$BUILD_NUMBER is running" \
         -f csv
}

function github_mark_failed_on_exit {
    trap '[ $? == "0" ] || github_status state:failed' EXIT
}
