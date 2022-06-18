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

"""This module sets up use of the Python logging module by the agent. As
we don't want to rely exclusively on the user having configured the
logging module themselves to capture any logged output we attach our own
log file when enabled from agent configuration. We also provide ability
to fallback to using stdout or stderr.

"""

import logging
import sys
import threading
import warnings

_lock = threading.Lock()


class _NullHandler(logging.Handler):
    def emit(self, record):
        pass


_agent_logger = logging.getLogger("newrelic")
_agent_logger.addHandler(_NullHandler())
_agent_logger.propagate = False

_LOG_FORMAT = "%(asctime)s (%(process)d/%(threadName)s) %(name)s %(levelname)s - %(message)s"

_initialized = False


def _initialize_stdout_logging(log_level):
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(_LOG_FORMAT)
    handler.setFormatter(formatter)

    _agent_logger.addHandler(handler)
    _agent_logger.setLevel(log_level)

    _agent_logger.debug("Initializing Python agent stdout logging.")


def _initialize_stderr_logging(log_level):
    handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(_LOG_FORMAT)
    handler.setFormatter(formatter)

    _agent_logger.addHandler(handler)
    _agent_logger.setLevel(log_level)

    _agent_logger.debug("Initializing Python agent stderr logging.")


def _initialize_file_logging(log_file, log_level):
    handler = logging.FileHandler(log_file)

    formatter = logging.Formatter(_LOG_FORMAT)
    handler.setFormatter(formatter)

    _agent_logger.addHandler(handler)
    _agent_logger.setLevel(log_level)

    _agent_logger.debug("Initializing Python agent logging.")
    _agent_logger.debug('Log file "%s".' % log_file)


def initialize_logging(log_file, log_level):
    global _initialized

    if _initialized:
        return

    _lock.acquire()

    try:
        if log_file == "stdout":
            _initialize_stdout_logging(log_level)

        elif log_file == "stderr":
            _initialize_stderr_logging(log_level)

        elif log_file:
            try:
                _initialize_file_logging(log_file, log_level)

            except Exception:
                _initialize_stderr_logging(log_level)

                _agent_logger.exception("Falling back to stderr logging as unable to create log file %r." % log_file)

        _initialized = True

    finally:
        _lock.release()


# This is to filter out the overly verbose log messages at INFO level
# made by the urllib3 module.


class Urllib3ConnectionFilter(logging.Filter):
    def filter(self, record):
        return False


_urllib3_logger = logging.getLogger("newrelic.packages.urllib3.connectionpool")
_urllib3_logger.addFilter(Urllib3ConnectionFilter())

# Also ignore any urllib3 warning messages
warnings.filterwarnings("ignore", module=r"newrelic\.packages\.urllib3")
