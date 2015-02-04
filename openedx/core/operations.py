import os
import signal
import tempfile

from datetime import datetime
from meliae import scanner


def dump_memory(signum, frame):
    """Dump memory stats for the current process to a temp directory. Uses the meliae output format."""
    scanner.dump_all_objects('{}/meliae.{}.{}.dump'.format(tempfile.gettempdir(), datetime.now().isoformat(), os.getpid()))

def install_memory_dumper(dump_signal=signal.SIGPROF):
    """
    Install a signal handler on `signal` to dump memory stats for the current process.
    """
    signal.signal(dump_signal, dump_memory)
