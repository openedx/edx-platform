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
    AUTHORED_BY=$($LOG_CMD --author="<${EMAIL}>" --format='tformat:%h')
    COMMITTED_BY=$($LOG_CMD --committer="<${EMAIL}>" --format='tformat:%h')
    ALL_COMMITS=$(for HASH in $AUTHORED_BY $COMMITTED_BY; do echo $HASH; done | sort | uniq)

    EMAIL_COL="$EMAIL"
    for HASH in $ALL_COMMITS; do
        git --no-pager log --format="tformat:|$EMAIL_COL|%s|[commit|https://github.com/edx/edx-platform/commit/%h]| |" -n 1 $HASH
        EMAIL_COL=" "
    done
done
