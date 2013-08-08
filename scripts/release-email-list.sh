#! /bin/bash
# Usage: release-email-list.sh [$PREVIOUS_COMMIT [$CURRENT_COMMIT]]
#
# Prints a list of email addresses and a Confluence style wiki table
# that indicate all of the changes made between $PREVIOUS_COMMIT and $CURRENT_COMMIT
#
# PREVIOUS_COMMIT defaults to origin/release
# CURRENT_COMMIT defaults to HEAD

BASE=${1:-origin/release}
CURRENT=${2:-HEAD}
LOG_CMD="git --no-pager log $BASE..$CURRENT"

RESPONSIBLE=$(sort -u <($LOG_CMD --format='tformat:%ae' && $LOG_CMD --format='tformat:%ce'))

echo "Comparing $BASE to $CURRENT"

echo "~~~~ Email ~~~~~"

echo -n 'To: '
echo ${RESPONSIBLE} | sed "s/ /, /g"
echo

echo "You've made changes that are about to be released. All of the commits
that you either authored or committed are listed below. Please verify them on
\$ENVIRONMENT.

Please record your notes on https://edx-wiki.atlassian.net/wiki/display/ENG/Release+Page%3A+\$DATE
and add any bugs found to the Release Candidate Bugs section"
echo

echo "~~~~~ Wiki Table ~~~~~"
echo "Type Ctrl+Shift+D on Confluence to embed the following table in your release wiki page"
echo

echo '||Author||Changes||Commit Link||Testing Notes||'

for EMAIL in $RESPONSIBLE; do
    AUTHORED_BY="$LOG_CMD --author=<${EMAIL}>"
    COMMITTED_BY="$LOG_CMD --committer=<${EMAIL}>"
    COMMITTED_NOT_AUTHORED="$COMMITTED_BY $($AUTHORED_BY --format='tformat:^%h')"

    $AUTHORED_BY --format="tformat:|$EMAIL|%s|[commit|https://github.com/edx/edx-platform/commit/%h]| |" | head -n 1
    $AUTHORED_BY --format="tformat:| |%s|[commit|https://github.com/edx/edx-platform/commit/%h]| |" | tail  -n +2

    if [[ $($COMMITTED_NOT_AUTHORED) != "" ]]; then
        $COMMITTED_NOT_AUTHORED --format="tformat:|$EMAIL|%s|[commit|https://github.com/edx/edx-platform/commit/%h]|Committed, didn't author|" | head -n 1
        $COMMITTED_NOT_AUTHORED --format="tformat:| |%s|[commit|https://github.com/edx/edx-platform/commit/%h]| |" | tail -n +2
    fi
done