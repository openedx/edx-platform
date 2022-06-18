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

"""This module implements a higher level data sampler which sits atop and
manages the consumption of data from a data source.

"""

import logging

from newrelic.common.object_names import callable_name

_logger = logging.getLogger(__name__)

class DataSampler(object):

    def __init__(self, consumer, source, name, settings, **properties):
        self.consumer = consumer

        self.settings = settings
        self.source_properties = source(settings)

        self.factory = self.source_properties['factory']
        self.instance =  None

        self.merged_properties = dict(self.source_properties)
        self.merged_properties.update(properties)

        self.name = (name or self.merged_properties.get('name')
                or callable_name(source))

        self.group = self.merged_properties.get('group')

        if self.group:
            self.group = self.group.rstrip('/')

        self.guid = self.merged_properties.get('guid')

        if self.guid is None and hasattr(source, 'guid'):
            self.guid = source.guid

        self.version = self.merged_properties.get('version')

        if self.version is None and hasattr(source, 'version'):
            self.version = source.version

        environ = {}

        environ['consumer.name'] = consumer
        environ['consumer.vendor'] = 'New Relic'
        environ['producer.name'] = self.name
        environ['producer.group'] = self.group
        environ['producer.guid'] = self.guid
        environ['producer.version'] = self.version

        self.environ = environ

        _logger.debug('Initialising data sampler for %r.', self.environ)

    def start(self):
        if self.instance is None:
            self.instance = self.factory(self.environ)

            if self.instance is None:
                _logger.error('Failed to create instance of data source for '
                        '%r, returned None. Custom metrics from this data '
                        'source will not subsequently be available. If this '
                        'problem persists, please report this problem '
                        'to the provider of the data source.', self.environ)

        if hasattr(self.instance, 'start'):
            self.instance.start()

    def stop(self):
        if hasattr(self.instance, 'stop'):
            self.instance.stop()
        else:
            self.instance = None

    def metrics(self):
        if self.instance is None:
            return []

        if self.group:
            return (('%s/%s' % (self.group, key), value)
                    for key, value in self.instance())
        else:
            return self.instance()
