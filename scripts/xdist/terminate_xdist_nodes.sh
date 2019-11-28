#!/bin/bash
set -e

if [ -f pytest_worker_instance_ids.txt ]; then
    echo "Terminating xdist workers with pytest_worker_manager.py"
    xdist_worker_ids=$(<pytest_worker_instance_ids.txt)
    python scripts/xdist/pytest_worker_manager.py -a down --instance-ids ${xdist_worker_ids}
else
    echo "File: pytest_worker_instance_ids.txt not found"
fi
