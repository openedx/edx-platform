#!/usr/bin/env bash
# Set up worker node.

while getopts 'p:d:' opt; do
    case "$opt" in
	p) PYTHON_VERSION="$OPTARG";;
	d) DJANGO_REQUIREMENT="$OPTARG";;
	[?])
	    print >&2 "Usage: $0 -p python-version -d django-reqs-file"
	    exit 1
            ;;
    esac
done

venv_parent=/home/jenkins/edx-venv-${PYTHON_VERSION}
venv=$venv_parent/edx-venv
rm -rf $venv
tar -C $venv_parent -xf /home/jenkins/edx-venv_clean-${PYTHON_VERSION}.tar.gz
source $venv/bin/activate

pip install -q -r ${DJANGO_REQUIREMENT} -r requirements/edx/testing.txt

mkdir reports
