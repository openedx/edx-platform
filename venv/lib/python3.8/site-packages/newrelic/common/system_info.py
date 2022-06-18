# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module implements functions for querying properties of the operating
system or for the specific process the code is running in.

"""

import logging
import multiprocessing
import os
import re
import socket
import subprocess
import sys
import threading

from newrelic.common.utilization import CommonUtilization

try:
    from subprocess import check_output as _execute_program
except ImportError:

    def _execute_program(*popenargs, **kwargs):
        # Replicates check_output() implementation from Python 2.7+.
        # Should only be used for Python 2.6.

        if "stdout" in kwargs:
            raise ValueError("stdout argument not allowed, it will be overridden.")
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)  # nosec
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd, output=output)
        return output


try:
    import resource
except ImportError:
    pass

_logger = logging.getLogger(__name__)

LOCALHOST_EQUIVALENTS = set(
    [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",  # nosec
        "0:0:0:0:0:0:0:0",
        "0:0:0:0:0:0:0:1",
        "::1",
        "::",
    ]
)


def logical_processor_count():
    """Returns the number of logical processors in the system."""

    # The multiprocessing module provides support for Windows,
    # BSD systems (including MacOS X) and systems which support
    # the POSIX API for querying the number of CPUs.

    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        pass

    # For Jython, we need to query the Java runtime environment.

    try:
        from java.lang import Runtime

        runtime = Runtime.getRuntime()
        res = runtime.availableProcessors()
        if res > 0:
            return res
    except ImportError:
        pass

    # Assuming that Solaris will support POSIX API for querying
    # the number of CPUs. Just in case though, work it out by
    # looking at the devices corresponding to the available CPUs.

    try:
        pseudoDevices = os.listdir("/devices/pseudo/")
        expr = re.compile("^cpuid@[0-9]+$")

        res = 0
        for pd in pseudoDevices:
            if expr.match(pd) is not None:
                res += 1

        if res > 0:
            return res
    except OSError:
        pass

    # Fallback to assuming only a single CPU.

    return 1


def _linux_physical_processor_count(filename=None):
    # For Linux we can use information from '/proc/cpuinfo.

    # A line in the file that starts with 'processor' marks the
    # beginning of a section.
    #
    # Multi-core processors will have a 'processor' section for each
    # core. There is usually a 'physical id' field and a 'cpu cores'
    # field as well.  The 'physical id' field in each 'processor'
    # section will have the same value for all cores in a physical
    # processor. The 'cpu cores' field for each 'processor' section will
    # provide the total number of cores for that physical processor.
    # The 'cpu cores' field is duplicated, so only remember the last

    filename = filename or "/proc/cpuinfo"

    processors = 0
    physical_processors = {}

    try:
        with open(filename, "r") as fp:
            processor_id = None
            cores = None

            for line in fp:
                try:
                    key, value = line.split(":")
                    key = key.lower().strip()
                    value = value.strip()

                except ValueError:
                    continue

                if key == "processor":
                    processors += 1

                    # If this is not the first processor section
                    # and prior sections specified a physical ID
                    # and number of cores, we want to remember
                    # the number of cores corresponding to that
                    # physical core. Note that we may see details
                    # for the same phyiscal ID more than one and
                    # thus we only end up remember the number of
                    # cores from the last one we see.

                    if cores and processor_id:
                        physical_processors[processor_id] = cores

                        processor_id = None
                        cores = None

                elif key == "physical id":
                    processor_id = value

                elif key == "cpu cores":
                    cores = int(value)

        # When we have reached the end of the file, we now need to save
        # away the number of cores for the physical ID we saw in the
        # last processor section.

        if cores and processor_id:
            physical_processors[processor_id] = cores

    except Exception:
        pass

    num_physical_processors = len(physical_processors) or (processors if processors == 1 else None)
    num_physical_cores = sum(physical_processors.values()) or (processors if processors == 1 else None)

    return (num_physical_processors, num_physical_cores)


def _darwin_physical_processor_count():
    # For MacOS X we can use sysctl.

    physical_processor_cmd = ["/usr/sbin/sysctl", "-n", "hw.packages"]

    try:
        num_physical_processors = int(_execute_program(physical_processor_cmd, stderr=subprocess.PIPE))  # nosec
    except (subprocess.CalledProcessError, ValueError):
        num_physical_processors = None

    physical_core_cmd = ["/usr/sbin/sysctl", "-n", "hw.physicalcpu"]

    try:
        num_physical_cores = int(_execute_program(physical_core_cmd, stderr=subprocess.PIPE))  # nosec
    except (subprocess.CalledProcessError, ValueError):
        num_physical_cores = None

    return (num_physical_processors, num_physical_cores)


def physical_processor_count():
    """Returns the number of physical processors and the number of physical
    cores in the system as a tuple. One or both values may be None, if a value
    cannot be determined.

    """

    if sys.platform.startswith("linux"):
        return _linux_physical_processor_count()
    elif sys.platform == "darwin":
        return _darwin_physical_processor_count()

    return (None, None)


def _linux_total_physical_memory(filename=None):
    # For Linux we can use information from /proc/meminfo. Although the
    # units is given in the file, it is always in kilobytes so we do not
    # need to accommodate any other unit types beside 'kB'.

    filename = filename or "/proc/meminfo"

    try:
        parser = re.compile(r"^(?P<key>\S*):\s*(?P<value>\d*)\s*kB")

        with open(filename, "r") as fp:
            for line in fp.readlines():
                match = parser.match(line)
                if not match:
                    continue
                key, value = match.groups(["key", "value"])
                if key == "MemTotal":
                    memory_bytes = float(value) * 1024
                    return memory_bytes / (1024 * 1024)

    except Exception:
        pass


def _darwin_total_physical_memory():
    # For MacOS X we can use sysctl. The value queried from sysctl is
    # always bytes.

    command = ["/usr/sbin/sysctl", "-n", "hw.memsize"]

    try:
        return float(_execute_program(command, stderr=subprocess.PIPE)) / (1024 * 1024)  # nosec
    except subprocess.CalledProcessError:
        pass
    except ValueError:
        pass


def total_physical_memory():
    """Returns the total physical memory available in the system. Returns
    None if the value cannot be calculated.

    """

    if sys.platform.startswith("linux"):
        return _linux_total_physical_memory()
    elif sys.platform == "darwin":
        return _darwin_total_physical_memory()

    return 0


def _linux_physical_memory_used(filename=None):
    # For Linux we can use information from the proc filesystem. We use
    # '/proc/statm' as it easier to parse than '/proc/status' file. The
    # value queried from the file is always in bytes.
    #
    #   /proc/[number]/statm
    #          Provides information about memory usage, measured
    #          in pages. The columns are:
    #
    #              size       total program size
    #                         (same as VmSize in /proc/[number]/status)
    #              resident   resident set size
    #                         (same as VmRSS in /proc/[number]/status)
    #              share      shared pages (from shared mappings)
    #              text       text (code)
    #              lib        library (unused in Linux 2.6)
    #              data       data + stack
    #              dt         dirty pages (unused in Linux 2.6)

    filename = filename or "/proc/%d/statm" % os.getpid()

    try:
        with open(filename, "r") as fp:
            rss_pages = float(fp.read().split()[1])
            memory_bytes = rss_pages * resource.getpagesize()
            return memory_bytes / (1024 * 1024)

    except Exception:
        return 0


def physical_memory_used():
    """Returns the amount of physical memory used in MBs. Returns 0 if
    the value cannot be calculated.

    """

    # A value of 0 is returned by default rather than None as this value
    # can be used in metrics. As such has traditionally always been
    # returned as an integer to avoid checks at the point is used.

    if sys.platform.startswith("linux"):
        return _linux_physical_memory_used()

    # For all other platforms try using getrusage() if we have the
    # resource module available. The units returned can differ based on
    # platform. Assume 1024 byte blocks as default. Some platforms such
    # as Solaris will report zero for 'ru_maxrss', so we skip those.

    try:
        rusage = resource.getrusage(resource.RUSAGE_SELF)
    except NameError:
        pass
    else:
        if sys.platform == "darwin":
            # On MacOS X, despite the manual page saying the
            # value is in kilobytes, it is actually in bytes.

            memory_bytes = float(rusage.ru_maxrss)
            return memory_bytes / (1024 * 1024)

        elif rusage.ru_maxrss > 0:
            memory_kbytes = float(rusage.ru_maxrss)
            return memory_kbytes / 1024

    return 0


def _resolve_hostname(use_dyno_names, dyno_shorten_prefixes):
    dyno_name = os.environ.get("DYNO")
    if not use_dyno_names or not dyno_name:
        return socket.gethostname()

    for prefix in dyno_shorten_prefixes:
        if prefix and dyno_name.startswith(prefix):
            return "%s.*" % prefix

    return dyno_name


_nr_cached_hostname_lock = threading.Lock()
_nr_cached_ipaddress_lock = threading.Lock()

_nr_cached_hostname = None
_nr_cached_ip_address = None


def gethostname(use_dyno_names=False, dyno_shorten_prefixes=()):
    """Cache the output of socket.gethostname().

    Keeps the reported hostname consistent throughout an agent run.

    """

    global _nr_cached_hostname
    global _nr_cached_hostname_lock

    if _nr_cached_hostname:
        return _nr_cached_hostname

    # Only lock for the one-time write.

    with _nr_cached_hostname_lock:
        if _nr_cached_hostname is None:
            _nr_cached_hostname = _resolve_hostname(use_dyno_names, dyno_shorten_prefixes)

    return _nr_cached_hostname


def getips():
    """Cache the output of socket.getsockname().

    Keeps the reported ips consistent throughout an agent run.

    """

    global _nr_cached_ip_address
    global _nr_cached_ipaddress_lock

    if _nr_cached_ip_address is not None:
        return _nr_cached_ip_address

    # Only lock for the one-time write.

    with _nr_cached_ipaddress_lock:
        if _nr_cached_ip_address is None:
            _nr_cached_ip_address = []

            try:
                # connect with UDP doesn't send packets (i.e. there's no
                # handshake like with TCP)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception:
                return _nr_cached_ip_address

            try:
                s.connect(("1.1.1.1", 1))
                _nr_cached_ip_address.append(s.getsockname()[0])
            except Exception:
                pass
            finally:
                s.close()

    return _nr_cached_ip_address


class BootIdUtilization(CommonUtilization):
    VENDOR_NAME = "boot_id"
    METADATA_URL = "/proc/sys/kernel/random/boot_id"

    @classmethod
    def fetch(cls):
        if not sys.platform.startswith("linux"):
            return

        try:
            with open(cls.METADATA_URL, "rb") as f:
                return f.readline().decode("ascii")
        except:
            # There are all sorts of exceptions that can occur here
            # (i.e. permissions, non-existent file, etc)
            cls.record_error(cls.METADATA_URL, "File read error.")
            pass

    @staticmethod
    def get_values(value):
        return value

    @classmethod
    def sanitize(cls, value):
        if value is None:
            return

        stripped = value.strip()

        if len(stripped) != 36:
            cls.record_error(cls.METADATA_URL, stripped)

        return stripped[:128] or None
