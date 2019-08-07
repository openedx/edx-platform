#!/usr/bin/env python
"""
List any modules that import code from the given package.  This can be used
to determine if the package can be safely removed, or just to understand
what context it's used in.  The package argument to the script should be
formatted as shown in these examples:

* scripts/dependencies/on_package.py nose
* scripts/dependencies/on_package.py third_parth_auth
* scripts/dependencies/on_package.py cms/djangoapps/verify_student

This script counts on scripts/dependencies/enumerate.sh having already
been run in order to generate a dependency data file to work from.
"""
from __future__ import absolute_import, print_function

import os
import re
import sys

pattern = re.compile(u'^{}'.format(sys.argv[1]))

data_path = 'reports/dependencies/dependencies.txt'
if not os.path.exists(data_path):
    print('The dependencies data file is unavailable; run scripts/dependencies/enumerate.sh first.')
with open(data_path, 'r') as f:
    for dep in map(eval, f):
        (from_root, from_name), (to_root, to_name) = dep
        if to_name is None:
            continue
        if pattern.search(to_name) and not pattern.search(from_name):
            # We usually don't care about dependencies between modules in site-packages
            if from_root.endswith(u'site-packages') and to_root.endswith(u'site-packages'):
                continue
            print(dep)
