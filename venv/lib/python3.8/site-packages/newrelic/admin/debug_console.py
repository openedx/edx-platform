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

@command('debug-console', 'config_file [session_log]',
"""Runs the client for the embedded agent debugging console.
""", hidden=True, log_intercept=False)
def debug_console(args):
    import sys

    if len(args) == 0:
        usage('debug-console')
        sys.exit(1)

    from newrelic.console import ClientShell

    config_file = args[0]
    log_object = None

    if len(args) >= 2:
        log_object = open(args[1], 'w')

    shell = ClientShell(config_file, log=log_object)
    shell.cmdloop()
