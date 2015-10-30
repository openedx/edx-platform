#!/bin/bash
if [ $# -eq 0 ]; then
    echo "$0: usage: rerun_0006.sh <arguments>. At minimum, '--settings=<environment>' is expected."
    exit 1
fi

./manage.py lms migrate course_groups 0005 --fake "$@"
./manage.py lms migrate course_groups 0006 "$@"
