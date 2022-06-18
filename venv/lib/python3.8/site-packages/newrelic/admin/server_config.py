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


@command('server-config', 'config_file [log_file]',
"""Dumps out the agent configuration after having loaded the settings
from <config_file>, registered the application and then merged the server
side configuration. The application name as specified in the agent
configuration file is used.""")
def server_config(args):
    import os
    import sys
    import logging
    import time

    if len(args) == 0:
        usage('server-config')
        sys.exit(1)

    from newrelic.api.application import register_application
    from newrelic.config import initialize

    if len(args) >= 2:
        log_file = args[1]
    else:
        log_file = '/tmp/python-agent-test.log'

    log_level = logging.DEBUG

    try:
        os.unlink(log_file)
    except Exception:
        pass

    config_file = args[0]
    environment = os.environ.get('NEW_RELIC_ENVIRONMENT')

    if config_file == '-':
        config_file = os.environ.get('NEW_RELIC_CONFIG_FILE')

    initialize(config_file, environment, ignore_errors=False,
            log_file=log_file, log_level=log_level)

    _timeout = 30.0

    _start = time.time()
    _application = register_application(timeout=_timeout)
    _end = time.time()

    _duration = _end - _start

    _logger = logging.getLogger(__name__)

    if not _application.active:
        _logger.error('Unable to register application for test, '
            'connection could not be established within %s seconds.',
            _timeout)
        return

    _logger.debug('Registration took %s seconds.', _duration)

    for key, value in sorted(_application.settings):
        print('%s = %r' % (key, value))
