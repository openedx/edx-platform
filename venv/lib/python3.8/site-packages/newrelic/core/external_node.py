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

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from collections import namedtuple

import newrelic.core.attribute as attribute
import newrelic.core.trace_node

from newrelic.core.node_mixin import GenericNodeMixin
from newrelic.core.metric import TimeMetric

_ExternalNode = namedtuple('_ExternalNode',
        ['library', 'url', 'method', 'children', 'start_time', 'end_time',
        'duration', 'exclusive', 'params', 'guid',
        'agent_attributes', 'user_attributes'])


class ExternalNode(_ExternalNode, GenericNodeMixin):

    @property
    def details(self):
        if hasattr(self, '_details'):
            return self._details

        try:
            self._details = urlparse.urlparse(self.url or '')
        except Exception:
            self._details = urlparse.urlparse('http://unknown.url')

        return self._details

    @property
    def name(self):
        return 'External/%s/%s/%s' % (
                self.netloc, self.library, self.method or '')

    @property
    def url_with_path(self):
        details = self.details
        url = urlparse.urlunsplit((details.scheme, details.netloc,
                details.path, '', ''))
        return url

    @property
    def http_url(self):
        if hasattr(self, '_http_url'):
            return self._http_url

        _, url_attr = attribute.process_user_attribute(
                'http.url', self.url_with_path)

        self._http_url = url_attr
        return url_attr

    @property
    def netloc(self):
        hostname = self.details.hostname or 'unknown'

        try:
            scheme = self.details.scheme.lower()
            port = self.details.port
        except Exception:
            scheme = None
            port = None

        if (scheme, port) in (('http', 80), ('https', 443)):
            port = None

        netloc = port and ('%s:%s' % (hostname, port)) or hostname
        return netloc

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        external node as well as all the child nodes.

        """

        yield TimeMetric(name='External/all', scope='',
                duration=self.duration, exclusive=self.exclusive)

        if root.type == 'WebTransaction':
            yield TimeMetric(name='External/allWeb', scope='',
                    duration=self.duration, exclusive=self.exclusive)
        else:
            yield TimeMetric(name='External/allOther', scope='',
                    duration=self.duration, exclusive=self.exclusive)

        netloc = self.netloc

        try:

            # Remove cross_process_id from the params dict otherwise it shows
            # up in the UI.

            self.cross_process_id = self.params.pop('cross_process_id')
            self.external_txn_name = self.params.pop('external_txn_name')
        except KeyError:
            self.cross_process_id = None
            self.external_txn_name = None

        name = 'External/%s/all' % netloc

        yield TimeMetric(name=name, scope='', duration=self.duration,
                  exclusive=self.exclusive)

        if self.cross_process_id is None:
            method = self.method or ''

            name = 'External/%s/%s/%s' % (netloc, self.library, method)

            yield TimeMetric(name=name, scope='', duration=self.duration,
                    exclusive=self.exclusive)

            yield TimeMetric(name=name, scope=root.path,
                    duration=self.duration, exclusive=self.exclusive)

        else:
            name = 'ExternalTransaction/%s/%s/%s' % (netloc,
                    self.cross_process_id, self.external_txn_name)

            yield TimeMetric(name=name, scope='', duration=self.duration,
                    exclusive=self.exclusive)

            yield TimeMetric(name=name, scope=root.path,
                    duration=self.duration, exclusive=self.exclusive)

            name = 'ExternalApp/%s/%s/all' % (netloc, self.cross_process_id)

            yield TimeMetric(name=name, scope='', duration=self.duration,
                    exclusive=self.exclusive)

    def trace_node(self, stats, root, connections):

        netloc = self.netloc

        method = self.method or ''

        if self.cross_process_id is None:
            name = 'External/%s/%s/%s' % (netloc, self.library, method)
        else:
            name = 'ExternalTransaction/%s/%s/%s' % (netloc,
                                                     self.cross_process_id,
                                                     self.external_txn_name)

        name = root.string_table.cache(name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        children = []

        root.trace_node_count += 1

        # Agent attributes
        self.agent_attributes['http.url'] = self.http_url

        params = self.get_trace_segment_params(
                root.settings, params=self.params)

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)

    def span_event(self, *args, **kwargs):
        self.agent_attributes['http.url'] = self.http_url
        attrs = super(ExternalNode, self).span_event(*args, **kwargs)
        i_attrs = attrs[0]

        i_attrs['category'] = 'http'
        i_attrs['span.kind'] = 'client'
        _, i_attrs['component'] = attribute.process_user_attribute(
                'component', self.library)

        if self.method:
            _, i_attrs['http.method'] = attribute.process_user_attribute(
                'http.method', self.method)

        return attrs
