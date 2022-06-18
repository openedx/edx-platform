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

from newrelic.common import system_info
from newrelic.core.node_mixin import DatastoreNodeMixin
from newrelic.core.metric import TimeMetric

_DatastoreNode = namedtuple('_DatastoreNode',
        ['product', 'target', 'operation', 'children', 'start_time',
        'end_time', 'duration', 'exclusive', 'host', 'port_path_or_id',
        'database_name', 'guid', 'agent_attributes', 'user_attributes'])


class DatastoreNode(_DatastoreNode, DatastoreNodeMixin):

    @property
    def instance_hostname(self):
        if self.host in system_info.LOCALHOST_EQUIVALENTS:
            hostname = system_info.gethostname()
        else:
            hostname = self.host
        return hostname

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        database node as well as all the child nodes.

        """

        product = self.product
        target = self.target
        operation = self.operation or 'other'

        # Determine the scoped metric

        statement_metric_name = 'Datastore/statement/%s/%s/%s' % (product,
                target, operation)

        operation_metric_name = 'Datastore/operation/%s/%s' % (product,
                operation)

        if target:
            scoped_metric_name = statement_metric_name
        else:
            scoped_metric_name = operation_metric_name

        yield TimeMetric(name=scoped_metric_name, scope=root.path,
                    duration=self.duration, exclusive=self.exclusive)

        # Unscoped rollup metrics

        yield TimeMetric(name='Datastore/all', scope='',
                duration=self.duration, exclusive=self.exclusive)

        yield TimeMetric(name='Datastore/%s/all' % product, scope='',
                duration=self.duration, exclusive=self.exclusive)

        if root.type == 'WebTransaction':
            yield TimeMetric(name='Datastore/allWeb', scope='',
                    duration=self.duration, exclusive=self.exclusive)

            yield TimeMetric(name='Datastore/%s/allWeb' % product, scope='',
                    duration=self.duration, exclusive=self.exclusive)
        else:
            yield TimeMetric(name='Datastore/allOther', scope='',
                    duration=self.duration, exclusive=self.exclusive)

            yield TimeMetric(name='Datastore/%s/allOther' % product, scope='',
                    duration=self.duration, exclusive=self.exclusive)

        # Unscoped operation metric

        yield TimeMetric(name=operation_metric_name, scope='',
                duration=self.duration, exclusive=self.exclusive)

        # Unscoped statement metric

        if target:
            yield TimeMetric(name=statement_metric_name, scope='',
                    duration=self.duration, exclusive=self.exclusive)

        # Unscoped instance Metric

        ds_tracer_settings = stats.settings.datastore_tracer

        if (self.instance_hostname and
                self.port_path_or_id and
                ds_tracer_settings.instance_reporting.enabled):

            instance_metric_name = 'Datastore/instance/%s/%s/%s' % (product,
                    self.instance_hostname, self.port_path_or_id)

            yield TimeMetric(name=instance_metric_name, scope='',
                    duration=self.duration, exclusive=self.exclusive)

    def trace_node(self, stats, root, connections):
        name = root.string_table.cache(self.name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        children = []

        root.trace_node_count += 1

        # Agent attributes
        self.agent_attributes['db.instance'] = self.db_instance
        params = self.get_trace_segment_params(root.settings)

        ds_tracer_settings = stats.settings.datastore_tracer
        instance_enabled = ds_tracer_settings.instance_reporting.enabled

        if instance_enabled:
            if self.instance_hostname:
                params['host'] = self.instance_hostname

            if self.port_path_or_id:
                params['port_path_or_id'] = self.port_path_or_id

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)

    def span_event(self, *args, **kwargs):
        if self.operation:
            self.agent_attributes["db.operation"] = self.operation
        return super(DatastoreNode, self).span_event(*args, **kwargs)
