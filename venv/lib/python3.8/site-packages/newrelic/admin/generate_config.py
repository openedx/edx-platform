# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

from newrelic.admin import command, usage

@command('generate-config', 'license_key [output_file]',
"""Generates a sample agent configuration file for <license_key>.""")
def generate_config(args):
    import os
    import sys

    if len(args) == 0:
        usage('generate-config')
        sys.exit(1)

    from newrelic import __file__ as package_root
    package_root = os.path.dirname(package_root)

    config_file = os.path.join(package_root, 'newrelic.ini')

    content = open(config_file, 'r').read()

    if len(args) >= 1:
        content = content.replace('*** REPLACE ME ***', args[0])

    if len(args) >= 2 and args[1] != '-':
        output_file = open(args[1], 'w')
        output_file.write(content)
        output_file.close()
    else:
        print(content)
