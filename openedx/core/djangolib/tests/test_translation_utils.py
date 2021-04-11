# -*- coding: utf-8 -*-
"""
Tests for openedx.core.djangolib.translation_utils
"""


import unittest

import datetime
import ddt

from openedx.core.djangolib.translation_utils import translate_date


@ddt.ddt
class TranslateDateTest(unittest.TestCase):
    """Test that we can convert the date object into a string with translation."""

    @ddt.data(
        (datetime.datetime(2018, 1, 21), u'21 de enero de 2018'),
        (datetime.datetime(2018, 2, 21), u'21 de febrero de 2018'),
        (datetime.datetime(2018, 3, 21), u'21 de marzo de 2018'),
        (datetime.datetime(2018, 4, 21), u'21 de abril de 2018'),
        (datetime.datetime(2018, 5, 21), u'21 de mayo de 2018'),
        (datetime.datetime(2018, 6, 21), u'21 de junio de 2018'),
        (datetime.datetime(2018, 7, 21), u'21 de julio de 2018'),
        (datetime.datetime(2018, 8, 21), u'21 de agosto de 2018'),
        (datetime.datetime(2018, 9, 21), u'21 de septiembre de 2018'),
        (datetime.datetime(2018, 10, 21), u'21 de octubre de 2018'),
        (datetime.datetime(2018, 11, 21), u'21 de noviembre de 2018'),
        (datetime.datetime(2018, 12, 21), u'21 de diciembre de 2018'),
    )
    @ddt.unpack
    def test_date_translate_in_spanish(self, date_to_translate, expected_translated_date):
        """
        Tests that date is correctly translating in spanish language
        """
        date_in_spanish = translate_date(date_to_translate, 'es')
        self.assertEqual(date_in_spanish, expected_translated_date)

    @ddt.data(
        (datetime.datetime(2018, 1, 21), u'Jan. 21, 2018'),
        (datetime.datetime(2018, 2, 21), u'Feb. 21, 2018'),
        (datetime.datetime(2018, 3, 21), u'March 21, 2018'),
        (datetime.datetime(2018, 4, 21), u'April 21, 2018'),
        (datetime.datetime(2018, 5, 21), u'May 21, 2018'),
        (datetime.datetime(2018, 6, 21), u'June 21, 2018'),
        (datetime.datetime(2018, 7, 21), u'July 21, 2018'),
        (datetime.datetime(2018, 8, 21), u'Aug. 21, 2018'),
        (datetime.datetime(2018, 9, 21), u'Sept. 21, 2018'),
        (datetime.datetime(2018, 10, 21), u'Oct. 21, 2018'),
        (datetime.datetime(2018, 11, 21), u'Nov. 21, 2018'),
        (datetime.datetime(2018, 12, 21), u'Dec. 21, 2018'),
    )
    @ddt.unpack
    def test_date_translate_to_default_language(self, date_to_translate, expected_translated_date):
        """
        Tests that date is correctly translating to default when language is not specified.
        """
        date_in_spanish = translate_date(date_to_translate, language=None)
        self.assertEqual(date_in_spanish, expected_translated_date)
