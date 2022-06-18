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

import newrelic.api.external_trace


def instrument(module):

    def url_request(rest_obj, method, url, *args, **kwargs):
        return url

    if hasattr(module, 'rest') and hasattr(module.rest, 'RESTClientObject'):
        newrelic.api.external_trace.wrap_external_trace(
                module, 'rest.RESTClientObject.request', 'dropbox',
                url_request)
