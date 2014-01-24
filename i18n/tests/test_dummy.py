# -*- coding: utf-8 -*-
"""Tests of i18n/dummy.py"""

from unittest import TestCase

import ddt
from polib import POEntry

from i18n import dummy


@ddt.ddt
class TestDummy(TestCase):
    """
    Tests functionality of i18n/dummy.py
    """

    def setUp(self):
        self.converter = dummy.Dummy()

    def assertUnicodeEquals(self, str1, str2):
        """Just like assertEquals, but doesn't put Unicode into the fail message.

        Either nose, or rake, or something, deals very badly with unusual
        Unicode characters in the assertions, so we use repr here to keep
        things safe.

        """
        self.assertEquals(
            str1, str2,
            "Mismatch: %r != %r" % (str1, str2),
        )

    @ddt.data(
        (u"hello my name is Bond, James Bond",
         u"héllø mý nämé ïs Bønd, Jämés Bønd Ⱡ'σяєм ι#"),

        (u"don't convert <a href='href'>tag ids</a>",
         u"døn't çønvért <a href='href'>täg ïds</a> Ⱡ'σяєм ιρѕυ#"),

        (u"don't convert %(name)s tags on %(date)s",
         u"døn't çønvért %(name)s tägs øn %(date)s Ⱡ'σяєм ιρѕ#"),
    )
    def test_dummy(self, data):
        """
        Tests with a dummy converter (adds spurious accents to strings).
        Assert that embedded HTML and python tags are not converted.
        """
        source, expected = data
        result = self.converter.convert(source)
        self.assertUnicodeEquals(result, expected)

    def test_singular(self):
        entry = POEntry()
        entry.msgid = "A lovely day for a cup of tea."
        expected = u"À løvélý däý før ä çüp øf téä. Ⱡ'σяєм #"
        self.converter.convert_msg(entry)
        self.assertUnicodeEquals(entry.msgstr, expected)

    def test_plural(self):
        entry = POEntry()
        entry.msgid = "A lovely day for a cup of tea."
        entry.msgid_plural = "A lovely day for some cups of tea."
        expected_s = u"À løvélý däý før ä çüp øf téä. Ⱡ'σяєм #"
        expected_p = u"À løvélý däý før sømé çüps øf téä. Ⱡ'σяєм ιρ#"
        self.converter.convert_msg(entry)
        result = entry.msgstr_plural
        self.assertUnicodeEquals(result['0'], expected_s)
        self.assertUnicodeEquals(result['1'], expected_p)
