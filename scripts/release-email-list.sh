#! /bin/bash

LOG_CMD="git --no-pager log $1..$2"

RESPONSIBLE=$(sort -u <($LOG_CMD --format='tformat:%ae' && $LOG_CMD --format='tformat:%ce'))

echo -n 'To: '
echo ${RESPONSIBLE} | sed "s/ /, /g"
echo

echo "You've made changes that are about to be released. All of the commits
that you either authored or committed are listed below. Please verify them on
\$ENVIRONMENT"
echo

for EMAIL in $RESPONSIBLE; do
    AUTHORED_BY="$LOG_CMD --author=<${EMAIL}>"
    COMMITTED_BY="$LOG_CMD --committer=<${EMAIL}>"
    COMMITTED_NOT_AUTHORED="$COMMITTED_BY $($AUTHORED_BY --format='tformat:^%h')"

    echo $EMAIL "authored the following commits:"
    $AUTHORED_BY --format='tformat:    %s - https://github.com/edx/edx-platform/commit/%h'
    echo

    if [[ $($COMMITTED_NOT_AUTHORED) != "" ]]; then
        echo $EMAIL "committed but didn't author the following commits:"
        $COMMITTED_NOT_AUTHORED --format='tformat:    %s - https://github.com/edx/edx-platform/commit/%h'
        echo
    fi
done