"""
A module to monitor certain files and have the modulestore reload courses.

Modified from
 http://stevelosh.com/blog/2011/06/django-advice/#watching-for-changes

NOTE: This code runs in a multi-process, multi-thread setting.  If you don't
understand threads or the gunicorn worker process environment, don't mess with
it :)

Basic structure:

- for each path being monitored, maintain a threading.Event object that is
  signalled when the file is changed.

- the client interface is the following:

1) Call watch(path) -> returns an Event object e.
2) call e.is_set() to tell whether the file has been modified.
3) call e.clear() to clear the state to start looking for the next modification.
4) go back to step 2 to ask about the next modification.
"""
import logging
import os
import time
import threading
import atexit
import Queue

log = logging.getLogger(__name__)


_interval = 1.0
_times = {}   # path -> modification time
_events = {}   # path -> event for that path

_queue = Queue.Queue()   # used only for thread-local sleeping
_running = False
_lock = threading.Lock()   # protects _running and writes to the _events dictionary

def _modified(path):
    """
    Check whether path has been modified.  If it has been, save the latest
    modification time in _times.
    """

    # Cases:
    #  - file has disappeared or changed type
    #  - file has appeared
    #  - file has been modified

    try:
        if not os.path.isfile(path):
            # was the file there before?
            if _times[path] > 0:
                _times[path] = 0   # now it's not here again
                return True
            # otherwise, nothing has changed
            return False

        # When was the file last modified?
        mtime = os.stat(path).st_mtime
        # has it changed?
        if mtime != _times[path]:
            _times[path] = mtime
            return True
    except:
        # If any exception occured, likely that file has been been removed just
        # before stat(), so say that it's been changed.
        return True

    return False

def _monitor():
    while True:
        # Check modification times on files which have
        # specifically been registered for monitoring.
        #log.debug("Watching %s", _events.keys())
        for path, event in _events.items():
            if _modified(path):
                # log.debug("%s modified", path)
                event.set()

        # Sleep for specified interval.
        try:
            return _queue.get(timeout=_interval)
        except:
            pass

_thread = threading.Thread(target=_monitor)
_thread.setDaemon(True)

def _exiting():
    try:
        _queue.put(True)
    except:
        pass
    _thread.join()

atexit.register(_exiting)

def watch(path):
    """
    Register path for watching.  Returns a threading.Event object that will be
    set after the file changes.  The caller is responsible for calling clear() on the event
    to find out about subsequent modifications.
    """
    _lock.acquire()

    if not path in _events:
        _events[path] = threading.Event()
        _times[path] = 0   # give it a dummy modification time to make logic earlier

    _lock.release()
    return _events[path]



def start(interval=1.0):
    global _interval
    if interval < _interval:
        _interval = interval

    global _running
    _lock.acquire()
    if not _running:
        prefix = 'monitor (pid=%d):' % os.getpid()
        log.info('{0}: Starting change monitor.'.format(prefix))
        _running = True
        _thread.start()
    _lock.release()
