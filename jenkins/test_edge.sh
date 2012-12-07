#! /bin/bash

set -e
set -x

source jenkins/base.sh

github_mark_failed_on_exit
github_status state:pending "is running"

# Reset the submodule, in case it changed
git submodule foreach 'git reset --hard HEAD'

# Set the IO encoding to UTF-8 so that askbot will start
export PYTHONIOENCODING=UTF-8

GIT_BRANCH=${GIT_BRANCH/HEAD/master}

pip install -q -r pre-requirements.txt
pip install -q -r test-requirements.txt
yes w | pip install -q -r requirements.txt

rake clobber
TESTS_FAILED=0
rake test_cms[false] || TESTS_FAILED=1
rake test_lms[false] || TESTS_FAILED=1
rake test_common/lib/capa || TESTS_FAILED=1
rake test_common/lib/xmodule || TESTS_FAILED=1
rake phantomjs_jasmine_lms || true
rake phantomjs_jasmine_cms || true
rake coverage:xml coverage:html

[ $TESTS_FAILED == '0' ]
rake autodeploy_properties

github_status state:success "passed"
