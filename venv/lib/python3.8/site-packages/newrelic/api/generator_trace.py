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
import types
import sys

from newrelic.api.time_trace import current_trace
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.common.object_names import callable_name


def GeneratorTraceWrapper(wrapped, name=None, group=None, label=None,
            params=None):

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

        def _generator(generator):
            _gname = '%s (generator)' % _name

            try:
                value = None
                exc = None

                while True:
                    parent = current_trace()

                    params = {}

                    frame = generator.gi_frame

                    params['filename'] = frame.f_code.co_filename
                    params['lineno'] = frame.f_lineno

                    with FunctionTrace(_gname, _group,
                             params=params, parent=parent):
                        try:
                            if exc is not None:
                                yielded = generator.throw(*exc)
                                exc = None
                            else:
                                yielded = generator.send(value)

                        except StopIteration:
                            break

                        except Exception:
                            raise

                    try:
                        value = yield yielded

                    except Exception:
                        exc = sys.exc_info()

            finally:
                generator.close()

        with FunctionTrace(_name, _group, _label, _params, parent=parent):
            try:
                result = wrapped(*args, **kwargs)

            except:  # Catch all
                raise

            else:
                if isinstance(result, types.GeneratorType):
                    return _generator(result)

                else:
                    return result

    return FunctionWrapper(wrapped, wrapper)


def generator_trace(name=None, group=None, label=None, params=None):
    return functools.partial(GeneratorTraceWrapper, name=name,
            group=group, label=label, params=params)


def wrap_generator_trace(module, object_path, name=None,
        group=None, label=None, params=None):
    return wrap_object(module, object_path, GeneratorTraceWrapper,
            (name, group, label, params))
