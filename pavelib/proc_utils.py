import sys
import os
import subprocess
import signal
import psutil


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


def run_process(processes, wait):

    kwargs = {'shell': True, 'cwd': None}
    pids = []

    try:
        for proc in processes:
            pids.extend([subprocess.Popen(proc, **kwargs)])

        if wait:
            signal.signal(signal.SIGINT, signal_handler)
            print("Enter CTL-C to end")
            signal.pause()
            print("Processes ending")
    except Exception, e:
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
