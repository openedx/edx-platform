"""
Workflows useful for reporting on runtime characteristics of the system
"""
import os
import signal
import tempfile
import gc

from datetime import datetime
from meliae import scanner


def dump_memory(signum, frame):
    """
    Dump memory stats for the current process to a temp directory.
    Uses the meliae output format.
    """

    timestamp = datetime.now().isoformat()
    format_str = '{}/meliae.{}.{}.{{}}.dump'.format(
        tempfile.gettempdir(),
        timestamp,
        os.getpid(),
    )

    scanner.dump_all_objects(format_str.format('pre-gc'))

    # force garbarge collection
    for gen in xrange(3):
        gc.collect(gen)
        scanner.dump_all_objects(
            format_str.format("gc-gen-{}".format(gen))
        )


def install_memory_dumper(dump_signal=signal.SIGPROF):
    """
    Install a signal handler on `signal` to dump memory stats for the current process.
    """
    signal.signal(dump_signal, dump_memory)
