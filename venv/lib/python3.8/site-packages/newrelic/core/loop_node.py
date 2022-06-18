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

from collections import namedtuple

import newrelic.core.trace_node

from newrelic.core.node_mixin import GenericNodeMixin
from newrelic.core.metric import TimeMetric

_LoopNode = namedtuple('_LoopNode',
        ['fetch_name', 'start_time', 'end_time', 'duration', 'guid'])


class LoopNode(_LoopNode, GenericNodeMixin):

    @property
    def exclusive(self):
        return self.duration

    @property
    def agent_attributes(self):
        return {}

    @property
    def children(self):
        return ()

    @property
    def name(self):
        return self.fetch_name()

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        function node as well as all the child nodes.

        """

        name = 'EventLoop/Wait/%s' % self.name

        yield TimeMetric(name=name, scope='', duration=self.duration,
                exclusive=self.duration)

        yield TimeMetric(name=name, scope=root.path,
                duration=self.duration, exclusive=self.duration)

        name = 'EventLoop/Wait/all'

        # Create IO loop rollup metrics
        yield TimeMetric(name=name, scope='', duration=self.duration,
                exclusive=None)

        if root.type == 'WebTransaction':
            yield TimeMetric(name=name + 'Web', scope='',
                    duration=self.duration, exclusive=None)
        else:
            yield TimeMetric(name=name + 'Other', scope='',
                    duration=self.duration, exclusive=None)

    def trace_node(self, stats, root, connections):

        name = 'EventLoop/Wait/%s' % self.name

        name = root.string_table.cache(name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        root.trace_node_count += 1

        children = []

        # Agent attributes
        params = {
            'exclusive_duration_millis': 1000.0 * self.duration,
        }

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)

    def span_event(self, *args, **kwargs):
        attrs = super(LoopNode, self).span_event(*args, **kwargs)
        i_attrs = attrs[0]

        i_attrs['name'] = 'EventLoop/Wait/%s' % self.name

        return attrs
