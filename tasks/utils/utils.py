import re
import os
import time
import requests
import contextlib
import subprocess
from pygments.console import colorize

@contextlib.contextmanager
def chdir(dirname):
    '''Context manager for changing directories'''

    cwd = os.getcwd()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(cwd)

def singleton_process(cmd, logfile=None):
    if not process_is_running(cmd):
        if logfile:
            log = open(logfile, 'a')
        else:
            log = None

        print("Running {command}, redirecting output to {logfile}".format(command=' '.join(cmd),
                                                                      logfile=log and log.name))
        subprocess.Popen(cmd, log)
    else:
        print(colorize("darkblue", "Process {} already running, skipping".format(' '.join(cmd))))

def process_is_running(cmd):
    '''Checks whether a process is running'''

    if isinstance(cmd, list):
        cmd = ' '.join(cmd)

    s = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(cmd):
            return True
    return False

def wait_for_server(server, port):
    for i in range(20):
        attempts = 0
        try:
            response = requests.head("{server}:{port}".format(**locals()))
            if response.ok:
                return True
        except:
            time.sleep(1)

    return False
