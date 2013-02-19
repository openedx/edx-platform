"""Run a python process in a jail."""

# Instructions:
#   - AppArmor.md from xserver

import os, os.path
import resource
import shutil
import subprocess
import threading
import time

from .util import temp_directory

# TODO: limit too much stdout data?

# Configure the Python command

SANDBOX_POSSIBILITIES = [
    "~/mitx_all/python-sandbox/bin/python",
    "/usr/bin/python-sandbox",
]

for sandbox_python in SANDBOX_POSSIBILITIES:
    sandbox_python = os.path.expanduser(sandbox_python)
    if os.path.exists(sandbox_python):
        PYTHON_CMD = [
            'sudo', '-u', 'sandbox',
            sandbox_python, '-E',
        ]
        break
else:
    raise Exception("Couldn't find Python sandbox")


class JailResult(object):
    """A passive object for us to return from jailpy."""
    pass

def jailpy(code, files=None, argv=None, stdin=None):
    """
    Run Python code in a jailed subprocess.

    `code` is a string containing the Python code to run.

    `files` is a list of file paths.

    Return an object with:

        .stdout: stdout of the program, a string
        .stderr: stderr of the program, a string
        .status: return status of the process: an int, 0 for successful

    """
    with temp_directory(delete_when_done=True) as tmpdir:

        # All the supporting files are copied into our directory.
        for filename in files or ():
            dest = os.path.join(tmpdir, os.path.basename(filename))
            shutil.copyfile(filename, dest)

        # Create the main file.
        with open(os.path.join(tmpdir, "jailed_code.py"), "w") as jailed:
            jailed.write(code)

        cmd = PYTHON_CMD + ['jailed_code.py'] + (argv or [])

        subproc = subprocess.Popen(
            cmd, preexec_fn=set_process_limits, cwd=tmpdir,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

        # TODO: time limiting

        killer = ProcessKillerThread(subproc)
        killer.start()
        result = JailResult()
        result.stdout, result.stderr = subproc.communicate(stdin)
        result.status = subproc.returncode

    return result


def set_process_limits():
    """
    Set limits on this processs, to be used first in a child process.
    """
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))     # 1 second of CPU--not wall clock time
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))   # no subprocesses
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))   # no files

    mem = 32 * 2**20     # 32 MB should be enough for anyone, right? :)
    resource.setrlimit(resource.RLIMIT_STACK, (mem, mem))
    resource.setrlimit(resource.RLIMIT_RSS, (mem, mem))
    resource.setrlimit(resource.RLIMIT_DATA, (mem, mem))


class ProcessKillerThread(threading.Thread):
    def __init__(self, subproc, limit=1):
        super(ProcessKillerThread, self).__init__()
        self.subproc = subproc
        self.limit = limit

    def run(self):
        start = time.time()
        while (time.time() - start) < self.limit:
            time.sleep(.1)
            if self.subproc.poll() is not None:
                # Process ended, no need for us any more.
                return

        if self.subproc.poll() is None:
            # Can't use subproc.kill because we launched the subproc with sudo.
            killargs = ["sudo", "kill", "-9", str(self.subproc.pid)]
            kill = subprocess.Popen(killargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = kill.communicate()
            # TODO: This doesn't actually kill the process.... :(
