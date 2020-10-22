#!/bin/bash
set -e

if [ -f pytest_task_arns.txt ]; then
    echo "Terminating xdist containers with pytest_container_manager.py"
    xdist_task_arns=$(<pytest_task_arns.txt)
    python scripts/xdist/pytest_container_manager.py -a down --task_arns ${xdist_task_arns}
else
    echo "File: pytest_task_arns.txt not found"
fi
