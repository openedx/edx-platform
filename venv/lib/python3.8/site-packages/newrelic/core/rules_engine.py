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

import re

from collections import namedtuple

_NormalizationRule = namedtuple('_NormalizationRule',
        ['match_expression', 'replacement', 'ignore', 'eval_order',
        'terminate_chain', 'each_segment', 'replace_all'])


class NormalizationRule(_NormalizationRule):

    def __init__(self, *args, **kwargs):
        self.match_expression_re = re.compile(
            self.match_expression, re.IGNORECASE)

    def apply(self, string):
        count = 1
        if self.replace_all:
            count = 0

        return self.match_expression_re.subn(self.replacement, string, count)


class RulesEngine(object):

    def __init__(self, rules):
        self.__rules = []

        for rule in rules:
            kwargs = {}
            for name in map(str, rule.keys()):
                if name in NormalizationRule._fields:
                    kwargs[name] = rule[name]
            self.__rules.append(NormalizationRule(**kwargs))

        self.__rules = sorted(self.__rules, key=lambda rule: rule.eval_order)

    @property
    def rules(self):
        return self.__rules

    def normalize(self, string):
        # URLs are supposed to be ASCII but can get a
        # URL with illegal non ASCII characters. As the
        # rule patterns and replacements are Unicode
        # then can get Unicode conversion warnings or
        # errors when URL is converted to Unicode and
        # default encoding is ASCII. Thus need to
        # convert URL to Unicode as Latin-1 explicitly
        # to avoid problems with illegal characters.

        if isinstance(string, bytes):
            string = string.decode('Latin-1')

        final_string = string
        ignore = False
        for rule in self.__rules:
            if rule.each_segment:
                matched = False

                segments = final_string.split('/')

                # FIXME This fiddle is to skip leading segment
                # when splitting on '/' where it is empty.
                # Should the rule just be to skip any empty
                # segment when matching keeping it as empty
                # but not matched. Wouldn't then have to treat
                # this as special.

                if segments and not segments[0]:
                    rule_segments = ['']
                    segments = segments[1:]
                else:
                    rule_segments = []

                for segment in segments:
                    rule_segment, match_count = rule.apply(segment)
                    matched = matched or (match_count > 0)
                    rule_segments.append(rule_segment)

                if matched:
                    final_string = '/'.join(rule_segments)
            else:
                rule_string, match_count = rule.apply(final_string)
                matched = match_count > 0
                final_string = rule_string

            if matched:
                ignore = ignore or rule.ignore

            if matched and rule.terminate_chain:
                break

        return (final_string, ignore)


class SegmentCollapseEngine(object):
    """Segment names in transaction name are collapsed using the rules
    from the data collector. The collector sends a prefix and list of
    whitelist terms associated with that prefix. If a transaction name
    matches the prefix then we replace all segments of the name with a
    '*' except for the segments in the whitelist terms.

    """

    COLLAPSE_STAR_RE = re.compile(r'((?:^|/)\*)(?:/\*)*')

    def __init__(self, rules):
        self.rules = {}

        prefixes = []

        for rule in rules:
            # Prefix should only have two segments, but believe there
            # may be a possibility of getting an extraneous trailing
            # slash. Therefore remove any trailing slashes. Technically
            # we can do away with the check for two segments, or at
            # least allow minimum of two and the algorithm will still
            # work as the regex for pre match and how remainder is
            # collected from pattern, will deal with prefixes of
            # different length and will choose the longest match.

            prefix_segments = rule['prefix'].rstrip('/').split('/')

            if len(prefix_segments) == 2:
                prefix = '/'.join(prefix_segments)
                self.rules[prefix] = rule['terms']
                prefixes.append(prefix)

        # Construct a regular expression which can efficiently pre match
        # any transaction name so we can avoid needing to split the
        # transaction name into segments.
        #
        # The pattern requires there to be at least one character in the
        # third segment. So three segments with the third being empty is
        # a special case that will always be passed through as is, even
        # if the prefix matched. We add a group around the remainder after
        # the prefix and immediately following slash so we only split on
        # that later if necessary.
        #
        # Use Unicode here when constructing pattern as the data collector
        # should always return prefixes and term strings as Unicode.

        choices = u'|'.join([re.escape(x) for x in prefixes])
        pattern = u'^(%s)/(.+)$' % choices

        self.prefixes = re.compile(pattern)

    def normalize(self, txn_name):
        """Takes a transaction name and collapses the segments into a
        '*' except for the segments in the whitelist_terms.

        Returns a modified copy of the transaction name and a flag
        indicating whether the transaction should be ignored. For
        segment rules there is currently no functionality to ignore the
        transaction based on a match, so we will always return False.

        """

        # If we have no rules then nothing to do.

        if not self.rules:
            return txn_name, False

        # Use our regular expression to perform a pre match so can avoid
        # needing to split the name into segments. This also gives us the
        # prefix which matched so we can check if we did in fact have
        # any terms for it.

        match = self.prefixes.match(txn_name)

        if not match:
            return txn_name, False

        prefix = match.group(1)

        whitelist_terms = self.rules.get(prefix)

        if whitelist_terms is None:
            return txn_name, False

        # Now split the name into segments. The name could be either a
        # byte string or a Unicode string. The separator will be coerced
        # to the correct type as necessary and the segments will always
        # be of the same type as the original name was. We shouldn't
        # therefore need to have to worry about Unicode issues and
        # whether a byte string contains anything which can't be changed
        # to a Unicode string as no coercion will occur.

        remainder = match.group(2)
        segments = remainder.split('/')

        # Replace non-whitelist terms with '*' and then collapse any
        # adjacent '*' segments to a single '*'.

        result = [x if x in whitelist_terms else '*' for x in segments]
        result = self.COLLAPSE_STAR_RE.sub('\\1', '/'.join(result))

        return '/'.join((prefix, result)), False
