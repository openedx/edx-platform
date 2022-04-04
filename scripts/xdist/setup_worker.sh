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

# Hack to fix up egg-link files given that the virtualenv is not relocatable
sed -i "s|\(^/home/jenkins\)/shallow-clone|\1/edx-platform|" -- \
    $venv/lib/python*/site-packages/*.egg-link
pip install -qr requirements/edx/pip-tools.txt
pip-sync -q requirements/edx/testing.txt "${DJANGO_REQUIREMENT}"

mkdir reports
