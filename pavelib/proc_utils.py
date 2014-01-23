import sys
import os
import subprocess
import signal
import psutil
import time

from urllib2 import urlopen, URLError


def write_stderr(message):
    sys.stderr.write(message)
    sys.stderr.flush()


def signal_handler(signal, frame):
    print("\nEnding...")


def kill_process(proc):
    p1_group = psutil.Process(proc.pid)

    child_pids = p1_group.get_children(recursive=True)

    for child_pid in child_pids:
        os.kill(child_pid.pid, signal.SIGKILL)


def run_process(processes, wait, out_log=None, err_log=None):

    kwargs = {'shell': True, 'cwd': None}
    pids = []

    if out_log:
        out_log_file = open(out_log, 'w')
        kwargs['stdout'] = out_log_file

    if err_log:
        err_log_file = open(err_log, 'w')
        kwargs['stderr'] = err_log_file

    try:
        for proc in processes:
            pids.extend([subprocess.Popen(proc, **kwargs)])

        if wait:
            signal.signal(signal.SIGINT, signal_handler)
            print("Enter CTL-C to end")
            signal.pause()
            print("Processes ending")
    except Exception as e:
        write_stderr("Error running process %s\n" % e)
    finally:
        if wait:
            try:
                for pid in pids:
                    kill_process(pid)
            except KeyboardInterrupt:
                pass
            except:
                pass

    if not wait:
        return pids
    else:
        return None


# Wait for a server to respond with status 200 at "/"
def wait_for_server(server):
    attempts = 0
    status = False

    while attempts < 20:
        try:
            response = urlopen(server, timeout=10)
            if response.code == 200:
                status = True
                break
        except URLError:
            attempts += 1
            time.sleep(1)

    return status
