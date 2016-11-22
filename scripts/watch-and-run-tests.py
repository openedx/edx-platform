#!/usr/bin/env python

import time
import logging
import os
from watchdog.observers import Observer
from watchdog.tricks import ShellCommandTrick

log = logging.getLogger(__name__)

PYTHON_PATTERN = ['*.py']
JS_PATTERN = ['*.js', '*.coffee']

TO_WATCH = [{'watch_dir': 'cms/djangoapps',
             'patterns': PYTHON_PATTERN,
             'shell_command': 'rake fasttest_cms'},
            {'watch_dir': 'lms/djangoapps',
             'patterns': PYTHON_PATTERN,
             'shell_command': 'rake fasttest_lms'},
            {'watch_dir': 'common/djangoapps',
             'patterns': PYTHON_PATTERN,
             'shell_command': 'rake fasttest_lms; rake fasttest_cms'},
            {'watch_dir': 'common/lib/capa/capa',
             'patterns': PYTHON_PATTERN,
             'shell_command': 'rake test_common/lib/capa'},
            {'watch_dir': 'common/lib/xmodule/xmodule',
             'patterns': PYTHON_PATTERN,
             'shell_command': 'rake test_common/lib/xmodule; rake fasttest_lms; rake fasttest_cms'},
            {'watch_dir': 'common/lib/xmodule/xmodule',
             'patterns': JS_PATTERN,
             'shell_command': 'rake jasmine'},
            {'watch_dir': 'common/static/coffee',
             'patterns': JS_PATTERN,
             'shell_command': 'rake jasmine:common/static/coffee'},
            {'watch_dir': 'cms/static/coffee',
             'patterns': JS_PATTERN,
             'shell_command': 'rake jasmine:cms'},
            {'watch_dir': 'lms/static/coffee',
             'patterns': JS_PATTERN,
             'shell_command': 'rake jasmine:lms'},
            ]


def main():
    '''
    Watch each of the specified directories recursively, and run the
    appropriate tests whenever a file is changed.
    '''
    observer = Observer()
    for watch in TO_WATCH:
        path = os.path.abspath(os.path.normpath(watch['watch_dir']))
        handler = ShellCommandTrick(shell_command=watch['shell_command'],
                                    patterns=watch['patterns'],
                                    ignore_directories=True,
                                    wait_for_process=True)
        observer.schedule(handler, path, True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
