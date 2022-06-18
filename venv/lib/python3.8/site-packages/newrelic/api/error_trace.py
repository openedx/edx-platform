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

import functools
import warnings

from newrelic.api.time_trace import current_trace, notice_error
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object


class ErrorTrace(object):
    def __init__(
        self,
        ignore_errors=[],
        ignore=None,
        expected=None,
        status_code=None,
        parent=None,
    ):
        if parent is None:
            parent = current_trace()

        self._transaction = parent and parent.transaction
        self._ignore = ignore if ignore is not None else ignore_errors
        self._expected = expected
        self._status_code = status_code

        if ignore_errors:
            warnings.warn(
                (
                    "The ignore_errors argument is deprecated. Please use the "
                    "new ignore argument instead."
                ),
                DeprecationWarning,
            )

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        if exc is None or value is None or tb is None:
            return

        if self._transaction is None:
            return

        notice_error(
            error=(exc, value, tb),
            ignore=self._ignore,
            expected=self._expected,
            status_code=self._status_code,
        )


def ErrorTraceWrapper(
    wrapped, ignore_errors=[], ignore=None, expected=None, status_code=None
):
    def wrapper(wrapped, instance, args, kwargs):
        parent = current_trace()

        if parent is None:
            return wrapped(*args, **kwargs)

        with ErrorTrace(ignore_errors, ignore, expected, status_code, parent=parent):
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, wrapper)


def error_trace(ignore_errors=[], ignore=None, expected=None, status_code=None):
    return functools.partial(
        ErrorTraceWrapper,
        ignore_errors=ignore_errors,
        ignore=ignore,
        expected=expected,
        status_code=status_code,
    )


def wrap_error_trace(
    module, object_path, ignore_errors=[], ignore=None, expected=None, status_code=None
):
    wrap_object(
        module,
        object_path,
        ErrorTraceWrapper,
        (
            ignore_errors,
            ignore,
            expected,
            status_code,
        ),
    )
