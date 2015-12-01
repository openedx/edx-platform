#!/bin/bash

apt-get purge mongodb-10gen
cd /edx/app/edx_ansible/edx_ansible/playbooks
/edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook -i localhost, -c local run_role.yml -e 'role=mongo' -e 'mongo_create_users=True'

mongo localhost <<EOF
use edxapp;
 
db.createUser(
{
user: "edxapp",
pwd: "password",
roles: [ "readWrite" ]
}
);
 
use cs_comments_service;
 
db.createUser(
{
user: "cs_comments_service",
pwd: "cs_comments_service",
roles: [ "readWrite" ]
}
);
EOF