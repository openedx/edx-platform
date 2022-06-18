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

from newrelic.common.object_wrapper import wrap_function_wrapper

# This is NOT a fully-featured instrumentation for the motor library. Instead
# this is a monkey-patch of the motor library to work around a bug that causes
# the __name__ lookup on a MotorCollection object to fail. This bug was causing
# customer's applications to fail when they used motor in Tornado applications.


def _nr_wrapper_Motor_getattr_(wrapped, instance, args, kwargs):

    def _bind_params(name, *args, **kwargs):
        return name

    name = _bind_params(*args, **kwargs)

    if name.startswith('__') or name.startswith('_nr_'):
        raise AttributeError('%s class has no attribute %s. To access '
                'use object[%r].' % (instance.__class__.__name__,
                name, name))

    return wrapped(*args, **kwargs)


def patch_motor(module):
    if (hasattr(module, 'version_tuple') and
            module.version_tuple >= (0, 6)):
        return

    patched_classes = ['MotorClient', 'MotorReplicaSetClient', 'MotorDatabase',
            'MotorCollection']
    for patched_class in patched_classes:
        if hasattr(module, patched_class):
            wrap_function_wrapper(module, patched_class + '.__getattr__',
                    _nr_wrapper_Motor_getattr_)
