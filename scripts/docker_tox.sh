#!/bin/bash

mkdir -p /data/db
mongod --fork --logpath /tmp/mongod.log

# Clear the mongo database
# Note that this prevents us from running jobs in parallel on a single worker.
mongo --quiet --eval 'db.getMongo().getDBNames().forEach(function(i){db.getSiblingDB(i).dropDatabase()})'

tox
