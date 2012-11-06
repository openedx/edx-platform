#! /bin/bash

# Reset the submodule, in case it changed
git submodule foreach 'git reset --hard HEAD'

# Set the IO encoding to UTF-8 so that askbot will start
export PYTHONIOENCODING=UTF-8

GIT_BRANCH=${GIT_BRANCH/HEAD/master}

pip install -r pre-requirements.txt
yes w | pip install -r requirements.txt
[ ! -d askbot ] || pip install -r askbot/askbot_requirements.txt

# Install the latest entry points from xmodule
pip install --upgrade -e common/lib/xmodule

rake clobber
TESTS_FAILED=0
rake test_lms[false] || TESTS_FAILED=1
rake test_common/lib/capa || TESTS_FAILED=1
rake test_common/lib/xmodule || TESTS_FAILED=1
rake phantomjs_jasmine_cms || true

[ $TESTS_FAILED == '0' ]
rake autodeploy_properties