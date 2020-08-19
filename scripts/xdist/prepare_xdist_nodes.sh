#!/bin/bash
set -e

echo "Spinning up xdist workers with pytest_worker_manager.py"
python scripts/xdist/pytest_worker_manager.py -a up -n ${XDIST_NUM_WORKERS} \
-ami ${XDIST_WORKER_AMI} \
-type ${XDIST_INSTANCE_TYPE} \
-s ${XDIST_WORKER_SUBNET} \
-sg ${XDIST_WORKER_SECURITY_GROUP} \
-key ${XDIST_WORKER_KEY_NAME} \
-iam ${XDIST_WORKER_IAM_PROFILE_ARN}

# Need to map remote branch to local branch when fetching a branch other than master
if [ "$XDIST_GIT_BRANCH" == "master" ]; then
    XDIST_GIT_FETCH_STRING="$XDIST_GIT_BRANCH"
else
    XDIST_GIT_FETCH_STRING="$XDIST_GIT_BRANCH:$XDIST_GIT_BRANCH"
fi

theme_git_password=$(printf "%q" $THEME_USER_PASSWORD)

ip_list=$(<pytest_worker_ips.txt)
for ip in $(echo $ip_list | sed "s/,/ /g")
do
    worker_reqs_cmd="ssh -o StrictHostKeyChecking=no jenkins@$ip
    'if [ -e /home/jenkins/edx-platform ]; then rm -rf /home/jenkins/edx-platform; fi;
    git clone --branch master --depth 1 -q https://github.com/philanthropy-u/edx-platform.git; cd edx-platform;
    git fetch -fq origin ${XDIST_GIT_REFSPEC}; git checkout -q ${XDIST_GIT_BRANCH};
    if [ -e /home/jenkins/edx-venv ]; then rm -rf /home/jenkins/edx-venv; fi;
    mkdir /home/jenkins/edx-venv; tar -C /home/jenkins/ -xf /home/jenkins/edx-venv_clean.tar.gz;
    source ../edx-venv/bin/activate;
    pip install -r requirements/edx/testing.txt; mkdir reports;
    pip install -r requirements/philu/testing.txt;
    if [ -e /edx/src ]; then rm -rf /edx/src; fi;
    sudo mkdir -p /edx/src;
    sudo chmod 755 -R /edx/src;
    sudo chown -R jenkins:jenkins /edx/src;
    cd /edx/src;
    git clone https://philanthropyu:${theme_git_password}@github.com/philanthropy-u/philu-edx-theme.git;
    exit' & "


    cmd=$cmd$worker_reqs_cmd
done
cmd=$cmd"wait"

echo "Executing commmand: $cmd"
eval $cmd
