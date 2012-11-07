#! /bin/bash

set -e
set -x

# Reset the submodule, in case it changed
git submodule foreach 'git reset --hard HEAD'

# Set the IO encoding to UTF-8 so that askbot will start
export PYTHONIOENCODING=UTF-8

rake clobber
rake pep8 || echo "pep8 failed, continuing"
rake pylint || echo "pylint failed, continuing"
