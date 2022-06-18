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

import newrelic.core.attribute as attribute

from newrelic.core.attribute_filter import (DST_SPAN_EVENTS,
        DST_TRANSACTION_SEGMENTS)


class GenericNodeMixin(object):
    @property
    def processed_user_attributes(self):
        if hasattr(self, '_processed_user_attributes'):
            return self._processed_user_attributes

        self._processed_user_attributes = u_attrs = {}
        user_attributes = getattr(self, 'user_attributes', u_attrs)
        for k, v in user_attributes.items():
            k, v = attribute.process_user_attribute(k, v)
            u_attrs[k] = v
        return u_attrs

    def get_trace_segment_params(self, settings, params=None):
        _params = attribute.resolve_agent_attributes(
                self.agent_attributes,
                settings.attribute_filter,
                DST_TRANSACTION_SEGMENTS)

        if params:
            _params.update(params)

        _params.update(attribute.resolve_user_attributes(
                self.processed_user_attributes,
                settings.attribute_filter,
                DST_TRANSACTION_SEGMENTS))

        _params['exclusive_duration_millis'] = 1000.0 * self.exclusive
        return _params

    def span_event(
                self,
                settings,
                base_attrs=None,
                parent_guid=None,
                attr_class=dict):
        i_attrs = base_attrs and base_attrs.copy() or attr_class()
        i_attrs['type'] = 'Span'
        i_attrs['name'] = self.name
        i_attrs['guid'] = self.guid
        i_attrs['timestamp'] = int(self.start_time * 1000)
        i_attrs['duration'] = self.duration
        i_attrs['category'] = 'generic'

        if parent_guid:
            i_attrs['parentId'] = parent_guid

        a_attrs = attribute.resolve_agent_attributes(
                self.agent_attributes,
                settings.attribute_filter,
                DST_SPAN_EVENTS,
                attr_class=attr_class)

        u_attrs = attribute.resolve_user_attributes(
                self.processed_user_attributes,
                settings.attribute_filter,
                DST_SPAN_EVENTS,
                attr_class=attr_class)

        # intrinsics, user attrs, agent attrs
        return [i_attrs, u_attrs, a_attrs]

    def span_events(self,
            settings, base_attrs=None, parent_guid=None, attr_class=dict):

        yield self.span_event(
                settings,
                base_attrs=base_attrs,
                parent_guid=parent_guid,
                attr_class=attr_class)

        for child in self.children:
            for event in child.span_events(
                    settings,
                    base_attrs=base_attrs,
                    parent_guid=self.guid,
                    attr_class=attr_class):
                yield event


class DatastoreNodeMixin(GenericNodeMixin):

    @property
    def name(self):
        product = self.product
        target = self.target
        operation = self.operation or 'other'

        if target:
            name = 'Datastore/statement/%s/%s/%s' % (product, target,
                    operation)
        else:
            name = 'Datastore/operation/%s/%s' % (product, operation)

        return name

    @property
    def db_instance(self):
        if hasattr(self, '_db_instance'):
            return self._db_instance

        db_instance_attr = None
        if self.database_name:
            _, db_instance_attr = attribute.process_user_attribute(
                    'db.instance', self.database_name)

        self._db_instance = db_instance_attr
        return db_instance_attr

    def span_event(self, *args, **kwargs):
        self.agent_attributes['db.instance'] = self.db_instance
        attrs = super(DatastoreNodeMixin, self).span_event(*args, **kwargs)
        i_attrs = attrs[0]
        a_attrs = attrs[2]

        i_attrs['category'] = 'datastore'
        i_attrs['component'] = self.product
        i_attrs['span.kind'] = 'client'

        if self.instance_hostname:
            _, a_attrs['peer.hostname'] = attribute.process_user_attribute(
                    'peer.hostname', self.instance_hostname)
        else:
            a_attrs['peer.hostname'] = 'Unknown'

        peer_address = '%s:%s' % (
                self.instance_hostname or 'Unknown',
                self.port_path_or_id or 'Unknown')

        _, a_attrs['peer.address'] = attribute.process_user_attribute(
                'peer.address', peer_address)

        return attrs
