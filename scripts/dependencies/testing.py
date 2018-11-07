#!/usr/bin/env python
"""
List any dependencies on test modules in edx-platform from non-test modules.
Generally, there shouldn't be any; such a dependency could result in
ImportErrors in production where testing packages aren't installed.

This script counts on scripts/dependencies/enumerate.sh having already
been run in order to generate a dependency data file to work from.
"""
from __future__ import absolute_import, print_function

import os
import re
import sys

# Enumerate all the Python modules that should only be imported during test runs
pattern_fragments = [
    # Test modules within edx-platform
    r'/tests?\.py',                            # test.py, tests.py
    r'/tests?_[^/]*\.py',                      # test_*.py, tests_*.py
    r'/[^/]*_tests\.py',                       # *_tests.py
    r'/tests?/',                               # */test/*, */tests/*
    r'[cl]ms/.*/features/',                    # cms/*/features/*, lms/*/features/*
    r'/testing\.py',                           # testing.py
    r'/testutils\.py',                         # testutils.py
    r'/tests$',                                # tests/__init__.py
    r'conftest\.py',                           # conftest.py
    r'/envs/acceptance\.py',                   # cms/envs/acceptance.py, lms/envs/acceptance.py
    r'/envs/acceptance_docker\.py',            # cms/envs/acceptance.py, lms/envs/acceptance.py
    r'/factories\.py',                         # factories.py
    r'^terrain',                               # terrain/*
    r'/setup_models_to_send_test_emails\.py',  # setup_models_to_send_test_emails management command

    # Testing-only package dependencies
    r'^bs4',                                   # beautifulsoup4
    r'^before_after$',                         # before_after
    r'^bok_choy',                              # bok-choy
    r'^cssselect',                             # cssselect
    r'^factory',                               # factory_boy
    r'^freezegun',                             # freezegun
    r'^httpretty',                             # httpretty
    r'^moto',                                  # moto
    r'^nose',                                  # nose
    r'^pyquery',                               # pyquery
    r'^pytest.py$',                            # pytest
    r'^selenium',                              # selenium
    r'^singledispatch',                        # singledispatch
    r'^testfixtures',                          # testfixtures
]

test_pattern = re.compile('|'.join(pattern_fragments))

data_path = 'reports/dependencies/dependencies.txt'
if not os.path.exists(data_path):
    print('The dependencies data file is unavailable; run scripts/dependencies/enumerate.sh first.')
    sys.exit(1)
exit_status = 0
with open(data_path, 'r') as f:
    for dep in map(eval, f):
        (from_root, from_name), (to_root, to_name) = dep
        if to_name is None:
            continue
        if test_pattern.search(to_name) and not test_pattern.search(from_name):
            # snakefood sometimes picks a weird place to split the root path and filename
            if from_root.endswith('/tests'):
                continue
            # We usually don't care about dependencies between modules in site-packages
            if from_root.endswith(u'site-packages') and to_root.endswith(u'site-packages'):
                continue
            # Dependencies on django.test and waffle.testutils are ok
            if to_name.startswith(u'django/test') or to_name == u'waffle/testutils.py':
                continue
            # Dependencies within pavelib are ok
            if from_name.startswith(u'pavelib') and to_name.startswith(u'pavelib'):
                continue
            print(dep)
            exit_status = 1
sys.exit(exit_status)
