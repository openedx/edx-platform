#!/bin/bash
set -e

echo "Spinning up xdist containers with pytest_container_manager.py"
python scripts/xdist/pytest_container_manager.py -a up -n ${XDIST_NUM_TASKS} \
-t ${XDIST_CONTAINER_TASK_NAME} \
-s ${XDIST_CONTAINER_SUBNET} \
-sg ${XDIST_CONTAINER_SECURITY_GROUP}

# Need to map remote branch to local branch when fetching a branch other than master
if [ "$XDIST_GIT_BRANCH" == "master" ]; then
    XDIST_GIT_FETCH_STRING="$XDIST_GIT_BRANCH"
else
    XDIST_GIT_FETCH_STRING="$XDIST_GIT_BRANCH:$XDIST_GIT_BRANCH"
fi

ip_list=$(<pytest_task_ips.txt)
for ip in $(echo $ip_list | sed "s/,/ /g")
do
    container_reqs_cmd="ssh -o StrictHostKeyChecking=no ubuntu@$ip 'cd /edx/app/edxapp;
    git clone --branch master --depth 1 --no-tags -q https://github.com/edx/edx-platform.git; cd edx-platform;
    git fetch --depth=1 --no-tags -q origin ${XDIST_GIT_FETCH_STRING}; git checkout -q ${XDIST_GIT_BRANCH};
    source /edx/app/edxapp/edxapp_env; pip install -qr requirements/edx/testing.txt; mkdir reports' & "

    cmd=$cmd$container_reqs_cmd
done
cmd=$cmd"wait"

echo "Executing commmand: $cmd"
eval $cmd
