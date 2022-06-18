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

from newrelic.api.external_trace import wrap_external_trace

def instrument(module):

    def tsocket_open_url(socket, *args, **kwargs):
        scheme = 'socket' if socket._unix_socket else 'http'
        if socket.port:
            url = '%s://%s:%s' % (scheme, socket.host, socket.port)
        else:
            url = '%s://%s' % (scheme, socket.host)

        return url

    wrap_external_trace(module, 'TSocket.open', 'thrift', tsocket_open_url)
