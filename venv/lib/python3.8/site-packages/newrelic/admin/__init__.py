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

import sys
import logging

_builtin_plugins = [
    'debug_console',
    'generate_config',
    'license_key',
    'local_config',
    'network_config',
    'record_deploy',
    'run_program',
    'run_python',
    'server_config',
    'validate_config'
]

_commands = {}


def command(name, options='', description='', hidden=False,
        log_intercept=True, deprecated=False):
    def wrapper(callback):
        callback.name = name
        callback.options = options
        callback.description = description
        callback.hidden = hidden
        callback.log_intercept = log_intercept
        callback.deprecated = deprecated
        _commands[name] = callback
        return callback
    return wrapper


def usage(name):
    details = _commands[name]
    if details.deprecated:
        print("[WARNING] This command is deprecated and will be removed")
    print('Usage: newrelic-admin %s %s' % (name, details.options))


@command('help', '[command]', hidden=True)
def help(args):
    if not args:
        print('Usage: newrelic-admin command [options]')
        print()
        print("Type 'newrelic-admin help <command>'", end='')
        print("for help on a specific command.")
        print()
        print("Available commands are:")

        commands = sorted(_commands.keys())
        for name in commands:
            details = _commands[name]
            if not details.hidden:
                print(' ', name)

    else:
        name = args[0]

        if name not in _commands:
            print("Unknown command '%s'." % name, end=' ')
            print("Type 'newrelic-admin help' for usage.")

        else:
            details = _commands[name]

            print('Usage: newrelic-admin %s %s' % (name, details.options))
            if details.description:
                print()
                description = details.description
                if details.deprecated:
                    description = '[DEPRECATED] ' + description
                print(description)


def setup_log_intercept():
    # Send any errors or warnings to standard output as well so more
    # obvious as use may have trouble finding the relevant messages in
    # the agent log as it will be full of debug output as well.

    class FilteredStreamHandler(logging.StreamHandler):
        def emit(self, record):
            if len(logging.root.handlers) != 0:
                return

            if record.name.startswith('newrelic.packages'):
                return

            if record.levelno < logging.WARNING:
                return

            return logging.StreamHandler.emit(self, record)

    _stdout_logger = logging.getLogger('newrelic')
    _stdout_handler = FilteredStreamHandler(sys.stdout)
    _stdout_format = '%(levelname)s - %(message)s\n'
    _stdout_formatter = logging.Formatter(_stdout_format)
    _stdout_handler.setFormatter(_stdout_formatter)
    _stdout_logger.addHandler(_stdout_handler)


def load_internal_plugins():
    for name in _builtin_plugins:
        module_name = '%s.%s' % (__name__, name)
        __import__(module_name)


def load_external_plugins():
    try:
        import pkg_resources
    except ImportError:
        return

    group = 'newrelic.admin'

    for entrypoint in pkg_resources.iter_entry_points(group=group):
        __import__(entrypoint.module_name)


def main():
    try:
        if len(sys.argv) > 1:
            command = sys.argv[1]
        else:
            command = 'help'

        callback = _commands[command]

    except Exception:
        print("Unknown command '%s'." % command, end='')
        print("Type 'newrelic-admin help' for usage.")
        sys.exit(1)

    if callback.log_intercept:
        setup_log_intercept()

    callback(sys.argv[2:])


load_internal_plugins()
load_external_plugins()

if __name__ == '__main__':
    main()
