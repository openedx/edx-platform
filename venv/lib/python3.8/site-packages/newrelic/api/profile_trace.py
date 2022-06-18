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
import sys
import os

from newrelic.packages import six

from newrelic.api.time_trace import current_trace
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.common.object_names import callable_name

from newrelic import __file__ as AGENT_PACKAGE_FILE
AGENT_PACKAGE_DIRECTORY = os.path.dirname(AGENT_PACKAGE_FILE) + '/'


class ProfileTrace(object):

    def __init__(self, depth):
        self.function_traces = []
        self.maximum_depth = depth
        self.current_depth = 0

    def __call__(self, frame, event, arg):

        if event not in ['call', 'c_call', 'return', 'c_return',
                'exception', 'c_exception']:
            return

        parent = current_trace()

        if not parent:
            return

        # Not sure if setprofile() is reliable in the face of
        # coroutine systems based on greenlets so don't run
        # if we detect may be using greenlets.

        if (hasattr(sys, '_current_frames') and
                parent.thread_id not in sys._current_frames()):
            return

        co = frame.f_code
        func_name = co.co_name
        func_line_no = frame.f_lineno
        func_filename = co.co_filename

        def _callable_name():
            # A stack frame doesn't provide any information about the
            # original callable object. We thus need to try and
            # deduce what it is by searching through the stack
            # frame globals. This will still not work in many
            # cases, including lambdas, generator expressions,
            # and decorated attributes such as properties of
            # classes.

            try:
                if func_name in frame.f_globals:
                    if frame.f_globals[func_name].func_code is co:
                        return callable_name(frame.f_globals[func_name])

            except Exception:
                pass

            for name, obj in six.iteritems(frame.f_globals):
                try:
                    if obj.__dict__[func_name].func_code is co:
                        return callable_name(obj.__dict__[func_name])

                except Exception:
                    pass

        if event in ['call', 'c_call']:
            # Skip the outermost as we catch that with the root
            # function traces for the profile trace.

            if len(self.function_traces) == 0:
                self.function_traces.append(None)
                return

            if self.current_depth >= self.maximum_depth:
                self.function_traces.append(None)
                return

            if func_filename.startswith(AGENT_PACKAGE_DIRECTORY):
                self.function_traces.append(None)
                return

            if event == 'call':
                name = _callable_name()
                if not name:
                    name = '%s:%s#%s' % (func_filename, func_name,
                            func_line_no)
            else:
                name = callable_name(arg)
                if not name:
                    name = '%s:@%s#%s' % (func_filename, func_name,
                            func_line_no)

            function_trace = FunctionTrace(name=name, parent=parent)
            function_trace.__enter__()

            self.function_traces.append(function_trace)
            self.current_depth += 1

        elif event in ['return', 'c_return', 'c_exception']:
            if not self.function_traces:
                return

            try:
                function_trace = self.function_traces.pop()

            except IndexError:
                pass

            else:
                if function_trace:
                    function_trace.__exit__(None, None, None)
                    self.current_depth -= 1


def ProfileTraceWrapper(wrapped, name=None, group=None, label=None,
        params=None, depth=3):

    def wrapper(wrapped, instance, args, kwargs):
        parent = current_trace()

        if parent is None:
            return wrapped(*args, **kwargs)

        if callable(name):
            if instance is not None:
                _name = name(instance, *args, **kwargs)
            else:
                _name = name(*args, **kwargs)

        elif name is None:
            _name = callable_name(wrapped)

        else:
            _name = name

        if callable(group):
            if instance is not None:
                _group = group(instance, *args, **kwargs)
            else:
                _group = group(*args, **kwargs)

        else:
            _group = group

        if callable(label):
            if instance is not None:
                _label = label(instance, *args, **kwargs)
            else:
                _label = label(*args, **kwargs)

        else:
            _label = label

        if callable(params):
            if instance is not None:
                _params = params(instance, *args, **kwargs)
            else:
                _params = params(*args, **kwargs)

        else:
            _params = params

        with FunctionTrace(_name, _group, _label, _params, parent=parent):
            if not hasattr(sys, 'getprofile'):
                return wrapped(*args, **kwargs)

            profiler = sys.getprofile()

            if profiler:
                return wrapped(*args, **kwargs)

            sys.setprofile(ProfileTrace(depth))

            try:
                return wrapped(*args, **kwargs)

            finally:
                sys.setprofile(None)

    return FunctionWrapper(wrapped, wrapper)


def profile_trace(name=None, group=None, label=None, params=None, depth=3):
    return functools.partial(ProfileTraceWrapper, name=name,
            group=group, label=label, params=params, depth=depth)


def wrap_profile_trace(module, object_path, name=None,
        group=None, label=None, params=None, depth=3):
    return wrap_object(module, object_path, ProfileTraceWrapper,
            (name, group, label, params, depth))
