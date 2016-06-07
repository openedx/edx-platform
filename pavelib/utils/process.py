"""
Helper functions for managing processes.
"""
from __future__ import print_function
import sys
import os
import subprocess
import signal
import psutil
import atexit

from paver import tasks


def kill_process(proc):
    """
    Kill the process `proc` created with `subprocess`.
    """
    p1_group = psutil.Process(proc.pid)

    # pylint: disable=unexpected-keyword-arg
    child_pids = p1_group.get_children(recursive=True)

    for child_pid in child_pids:
        os.kill(child_pid.pid, signal.SIGKILL)


def run_multi_processes(cmd_list, out_log=None, err_log=None):
    """
    Run each shell command in `cmd_list` in a separate process,
    piping stdout to `out_log` (a path) and stderr to `err_log` (also a path).

    Terminates the processes on CTRL-C and ensures the processes are killed
    if an error occurs.
    """
    kwargs = {'shell': True, 'cwd': None}
    pids = []

    if out_log:
        out_log_file = open(out_log, 'w')
        kwargs['stdout'] = out_log_file

    if err_log:
        err_log_file = open(err_log, 'w')
        kwargs['stderr'] = err_log_file

    # If the user is performing a dry run of a task, then just log
    # the command strings and return so that no destructive operations
    # are performed.
    if tasks.environment.dry_run:
        for cmd in cmd_list:
            tasks.environment.info(cmd)
        return

    try:
        for cmd in cmd_list:
            pids.extend([subprocess.Popen(cmd, **kwargs)])

        # pylint: disable=unused-argument
        def _signal_handler(*args):
            """
            What to do when process is ended
            """
            print("\nEnding...")

        signal.signal(signal.SIGINT, _signal_handler)
        print("Enter CTL-C to end")
        signal.pause()
        print("Processes ending")

    # pylint: disable=broad-except
    except Exception as err:
        print("Error running process {}".format(err), file=sys.stderr)

    finally:
        for pid in pids:
            kill_process(pid)


def run_process(cmd, out_log=None, err_log=None):
    """
    Run the shell command `cmd` in a separate process,
    piping stdout to `out_log` (a path) and stderr to `err_log` (also a path).

    Terminates the process on CTRL-C or if an error occurs.
    """
    return run_multi_processes([cmd], out_log=out_log, err_log=err_log)


def run_background_process(cmd, out_log=None, err_log=None, cwd=None):
    """
    Runs a command as a background process. Sends SIGINT at exit.
    """

    kwargs = {'shell': True, 'cwd': cwd}
    if out_log:
        out_log_file = open(out_log, 'w')
        kwargs['stdout'] = out_log_file

    if err_log:
        err_log_file = open(err_log, 'w')
        kwargs['stderr'] = err_log_file

    proc = subprocess.Popen(cmd, **kwargs)

    def exit_handler():
        """
        Send SIGINT to the process's children. This is important
        for running commands under coverage, as coverage will not
        produce the correct artifacts if the child process isn't
        killed properly.
        """
        p1_group = psutil.Process(proc.pid)

        # pylint: disable=unexpected-keyword-arg
        child_pids = p1_group.get_children(recursive=True)

        for child_pid in child_pids:
            os.kill(child_pid.pid, signal.SIGINT)

        # Wait for process to actually finish
        proc.wait()

    atexit.register(exit_handler)
