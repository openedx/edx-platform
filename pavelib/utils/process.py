"""
Helper functions for managing processes.
"""

import sys
import os
import subprocess
import signal
import psutil


def write_stderr(message):
    """
    Print a `message` str to stderr.
    """
    sys.stderr.write(message)
    sys.stderr.flush()


def kill_process(proc):
    """
    Kill the process `proc` created with `subprocess`.
    """
    p1_group = psutil.Process(proc.pid)

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

    try:
        for cmd in cmd_list:
            pids.extend([subprocess.Popen(cmd, **kwargs)])

        def _signal_handler(*args):
            print("\nEnding...")

        signal.signal(signal.SIGINT, _signal_handler)
        print("Enter CTL-C to end")
        signal.pause()
        print("Processes ending")

    except Exception as err:
        write_stderr("Error running process {}\n".format(err))

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
