#! /usr/bin/env bash

export GITHUB_USER='edx-deployment'
export GITHUB_TOKEN=$GH_ACCESS_TOKEN
export GITHUB_EMAIL='edx-deployment@edx.org'
export REPO_NAME='edx-platform'
export DB_NAME='edxapp'

cd ..

# install hub
curl -L -o hub.tgz https://github.com/github/hub/releases/download/v2.14.2/hub-linux-amd64-2.14.2.tgz
tar -zxvf hub.tgz

cd "$REPO_NAME"

if [[ -z $(git status -s) ]]; then
    echo "No changes to commit."
else
    git config --global user.name "${GITHUB_USER}"
    git config --global user.email "${GITHUB_EMAIL}"

    obsolete_dump_prs=`../hub-linux*/bin/hub pr list -s open --format '%I:%H %n' | grep 'github-actions-mysqldbdump'`

    if [[ ! -z $obsolete_dump_prs ]]; then
      for pr in $obsolete_dump_prs; do
        IFS=':' read pr_num branch <<< "$pr"
        ../hub-linux*/bin/hub issue update ${pr_num} -s closed
        ../hub-linux*/bin/hub push origin --delete ${branch}
      done
    fi

    git checkout -b github-actions-mysqldbdump/$GITHUB_SHA
    git add "${DB_NAME}".sql
    git commit  -m "MySQLdbdump" --author "GitHub Actions MySQLdbdump automation <admin@edx.org>"
    git push --set-upstream origin github-actions-mysqldbdump/$GITHUB_SHA
    ../hub-linux*/bin/hub pull-request -m "${DB_NAME} MySQL database dump" -m "MySQL database dump" -l mysqldbdump

fi
