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

# Attribute "destinations" represented as bitfields.

DST_NONE = 0x0
DST_ALL  = 0x3F
DST_TRANSACTION_EVENTS   = 1 << 0
DST_TRANSACTION_TRACER   = 1 << 1
DST_ERROR_COLLECTOR      = 1 << 2
DST_BROWSER_MONITORING   = 1 << 3
DST_SPAN_EVENTS          = 1 << 4
DST_TRANSACTION_SEGMENTS = 1 << 5

class AttributeFilter(object):

    # Apply filtering rules to attributes.
    #
    # Upon initialization, an AttributeFilter object will take all attribute
    # related settings and turn them into an ordered tuple of
    # AttributeFilterRules. During registration of the agent, a single
    # AttributeFilter object will be created, and will remain unchanged for
    # the life of the agent run. Changing attribute related settings/rules
    # requires restarting the agent.
    #
    # Each attribute can belong to one or more destinations. To determine
    # which destination an attribute belongs to, call the apply() method,
    # which will apply all of the rules to the attribute and return a set of
    # destinations.
    #
    # Destinations are represented as bitfields, where the bit positions
    # specified in the DST_* constants are used to indicate which
    # destination an attribute belongs to.
    #
    # The algorithm for applying filtering rules is as follows:
    #
    #   1. Start with a bitfield representing the set of default destinations
    #      passed in to apply().
    #
    #   2. Mask this bitfield against the set of destinations that have
    #      attribute enabled at all.
    #
    #   3. Traverse the list of AttributeFilterRules in order, applying
    #      each matching rule, but taking care to not let rules override the
    #      enabled status of each destination. Each matching rule may mutate
    #      the bitfield.
    #
    #   4. Return the resulting bitfield after all rules have been applied.

    def __init__(self, flattened_settings):

        self.enabled_destinations = self._set_enabled_destinations(flattened_settings)
        self.rules = self._build_rules(flattened_settings)
        self.cache = {}

    def __repr__(self):
        return "<AttributeFilter: destinations: %s, rules: %s>" % (
                bin(self.enabled_destinations), self.rules)

    def _set_enabled_destinations(self, settings):

        # Determines and returns bitfield representing attribute destinations enabled.

        enabled_destinations = DST_NONE

        if settings.get('transaction_segments.attributes.enabled', None):
            enabled_destinations |= DST_TRANSACTION_SEGMENTS

        if settings.get('span_events.attributes.enabled', None):
            enabled_destinations |= DST_SPAN_EVENTS

        if settings.get('transaction_tracer.attributes.enabled', None):
            enabled_destinations |= DST_TRANSACTION_TRACER

        if settings.get('transaction_events.attributes.enabled', None):
            enabled_destinations |= DST_TRANSACTION_EVENTS

        if settings.get('error_collector.attributes.enabled', None):
            enabled_destinations |= DST_ERROR_COLLECTOR

        if settings.get('browser_monitoring.attributes.enabled', None):
            enabled_destinations |= DST_BROWSER_MONITORING

        if not settings.get('attributes.enabled', None):
            enabled_destinations = DST_NONE

        return enabled_destinations

    def _build_rules(self, settings):

        # "Rule Templates" below are used for building AttributeFilterRules.
        #
        # Each tuple includes:
        #   1. Setting name
        #   2. Bitfield value for destination for that setting.
        #   3. Boolean that represents whether the setting is an "include" or not.

        rule_templates = (
            ('attributes.include', DST_ALL, True),
            ('attributes.exclude', DST_ALL, False),
            ('transaction_events.attributes.include', DST_TRANSACTION_EVENTS, True),
            ('transaction_events.attributes.exclude', DST_TRANSACTION_EVENTS, False),
            ('transaction_tracer.attributes.include', DST_TRANSACTION_TRACER, True),
            ('transaction_tracer.attributes.exclude', DST_TRANSACTION_TRACER, False),
            ('error_collector.attributes.include', DST_ERROR_COLLECTOR, True),
            ('error_collector.attributes.exclude', DST_ERROR_COLLECTOR, False),
            ('browser_monitoring.attributes.include', DST_BROWSER_MONITORING, True),
            ('browser_monitoring.attributes.exclude', DST_BROWSER_MONITORING, False),
            ('span_events.attributes.include', DST_SPAN_EVENTS, True),
            ('span_events.attributes.exclude', DST_SPAN_EVENTS, False),
            ('transaction_segments.attributes.include', DST_TRANSACTION_SEGMENTS, True),
            ('transaction_segments.attributes.exclude', DST_TRANSACTION_SEGMENTS, False),
        )

        rules = []

        for (setting_name, destination, is_include) in rule_templates:

            for setting in settings.get(setting_name) or ():
                rule = AttributeFilterRule(setting, destination, is_include)
                rules.append(rule)

        rules.sort()

        return tuple(rules)

    def apply(self, name, default_destinations):
        if self.enabled_destinations == DST_NONE:
            return DST_NONE

        cache_index = (name, default_destinations)

        if cache_index in self.cache:
            return self.cache[cache_index]

        destinations = self.enabled_destinations & default_destinations

        for rule in self.rules:
            if rule.name_match(name):
                if rule.is_include:
                    inc_dest = rule.destinations & self.enabled_destinations
                    destinations |= inc_dest
                else:
                    destinations &= ~rule.destinations

        self.cache[cache_index] = destinations
        return destinations

class AttributeFilterRule(object):

    def __init__(self, name, destinations, is_include):
        self.name = name.rstrip('*')
        self.destinations = destinations
        self.is_include = is_include
        self.is_wildcard = name.endswith('*')

    def _as_sortable(self):

        # Represent AttributeFilterRule as a tuple that will sort properly.
        #
        # Sorting rules:
        #
        #   1. Rules are sorted lexicographically by name, so that shorter,
        #      less specific names come before longer, more specific ones.
        #
        #   2. If names are the same, then rules with wildcards come before
        #      non-wildcards. Since False < True, we need to invert is_wildcard
        #      in the tuple, so that rules with wildcards have precedence.
        #
        #   3. If names and wildcards are the same, then include rules come
        #      before exclude rules. Similar to rule above, we must invert
        #      is_include for correct sorting results.
        #
        # By taking the sorted rules and applying them in order against an
        # attribute, we will guarantee that the most specific rule is applied
        # last, in accordance with the Agent Attributes spec.

        return (self.name, not self.is_wildcard, not self.is_include)

    def __eq__(self, other):
        return self._as_sortable() == other._as_sortable()

    def __ne__(self, other):
        return self._as_sortable() != other._as_sortable()

    def __lt__(self, other):
        return self._as_sortable() < other._as_sortable()

    def __le__(self, other):
        return self._as_sortable() <= other._as_sortable()

    def __gt__(self, other):
        return self._as_sortable() > other._as_sortable()

    def __ge__(self, other):
        return self._as_sortable() >= other._as_sortable()

    def __repr__(self):
        return '(%s, %s, %s, %s)' % (self.name, bin(self.destinations),
                self.is_wildcard, self.is_include)

    def name_match(self, name):
        if self.is_wildcard:
            return name.startswith(self.name)
        else:
            return self.name == name
