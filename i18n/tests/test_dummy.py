import os, string, random
from unittest import TestCase
from polib import POEntry

import dummy


class TestDummy(TestCase):
    """
    Tests functionality of i18n/dummy.py
    """

    def setUp(self):
        self.converter = dummy.Dummy()

    def test_dummy(self):
        """
        Tests with a dummy converter (adds spurious accents to strings).
        Assert that embedded HTML and python tags are not converted.
        """
        test_cases = [
            ("hello my name is Bond, James Bond",
             u'h\xe9ll\xf8 m\xfd n\xe4m\xe9 \xefs B\xf8nd, J\xe4m\xe9s B\xf8nd Lorem i#'),

            ('don\'t convert <a href="href">tag ids</a>',
             u'd\xf8n\'t \xe7\xf8nv\xe9rt <a href="href">t\xe4g \xefds</a> Lorem ipsu#'),

            ('don\'t convert %(name)s tags on %(date)s',
             u"d\xf8n't \xe7\xf8nv\xe9rt %(name)s t\xe4gs \xf8n %(date)s Lorem ips#")
        ]
        for source, expected in test_cases:
            result = self.converter.convert(source)
            self.assertEquals(result, expected)

    def test_singular(self):
        entry = POEntry()
        entry.msgid = 'A lovely day for a cup of tea.'
        expected = u'\xc0 l\xf8v\xe9l\xfd d\xe4\xfd f\xf8r \xe4 \xe7\xfcp \xf8f t\xe9\xe4. Lorem i#'
        self.converter.convert_msg(entry)
        self.assertEquals(entry.msgstr, expected)

    def test_plural(self):
        entry = POEntry()
        entry.msgid = 'A lovely day for a cup of tea.'
        entry.msgid_plural = 'A lovely day for some cups of tea.'
        expected_s = u'\xc0 l\xf8v\xe9l\xfd d\xe4\xfd f\xf8r \xe4 \xe7\xfcp \xf8f t\xe9\xe4. Lorem i#'
        expected_p = u'\xc0 l\xf8v\xe9l\xfd d\xe4\xfd f\xf8r s\xf8m\xe9 \xe7\xfcps \xf8f t\xe9\xe4. Lorem ip#'
        self.converter.convert_msg(entry)
        result = entry.msgstr_plural
        self.assertEquals(result['0'], expected_s)
        self.assertEquals(result['1'], expected_p)
