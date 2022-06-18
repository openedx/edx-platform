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

from newrelic.api.post_function import wrap_post_function

def _patch_thread(threading=True, *args, **kwargs):
    # This is looking for evidence that are using gevent prior to
    # version 0.13.7. In those versions the threading._sleep() method
    # wasn't being patched, which would result in the agent not working.
    # We do our own patch comparable to what newer versions of gevent
    # are now doing to get things working.

    if threading:
        threading = __import__('threading')
        if hasattr(threading, '_sleep'):
            from gevent.hub import sleep
            if threading._sleep != sleep:
                threading._sleep = sleep

def instrument_gevent_monkey(module):
    wrap_post_function(module, 'patch_thread', _patch_thread)
