#! /usr/bin/env python

# This script requires that you have watchdog installed. You can install
# watchdog via 'pip install watchdog'

import sys
import time
import logging
import os
from subprocess import Popen
from signal import SIGTERM
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler

# To watch more (or more specific) directories, change WATCH_DIRS to include the
# directories you want to watch. Note that this is recursive. If you want to
# watch fewer or more extensions, you can change EXTENSIONS. To watch all
# extensions, add "*" to EXTENSIONS.

WATCH_DIRS = ["../data", "common/lib/xmodule/xmodule/js", "common/lib/xmodule/xmodule/css"]
EXTENSIONS = ["*", "xml", "js", "css", "coffee", "scss", "html"]

WATCH_DIRS = [os.path.abspath(os.path.normpath(dir)) for dir in WATCH_DIRS]

class DjangoEventHandler(FileSystemEventHandler):

    def __init__(self, process):
        super(DjangoEventHandler, self).__init__()

        self.process = process

    def on_any_event(self, event):
        for extension in EXTENSIONS:
            if event.src_path.endswith(extension) or extension == "*":
                print "%s changed: restarting server." % event.src_path
                os.system("touch lms/__init__.py")
                break

if __name__ == "__main__":
    event_handler = DjangoEventHandler(Popen(['paver', 'lms']))
    observer = Observer()
    for dir in WATCH_DIRS:
        observer.schedule(event_handler, dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
