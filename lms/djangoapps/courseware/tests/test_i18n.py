"""
Tests i18n in courseware
"""
import re
from nose.plugins.attrib import attr

from django.test import TestCase
from django.test.utils import override_settings


@attr('shard_1')
@override_settings(LANGUAGES=[('eo', 'Esperanto'), ('ar', 'Arabic')])
class I18nTestCase(TestCase):
    """
    Tests for i18n
    """
    def assert_tag_has_attr(self, content, tag, attname, value):
        """Assert that a tag in `content` has a certain value in a certain attribute."""
        regex = r"""<{tag} [^>]*\b{attname}=['"]([\w\d ]+)['"][^>]*>""".format(tag=tag, attname=attname)
        match = re.search(regex, content)
        self.assertTrue(match, "Couldn't find desired tag in %r" % content)
        attvalues = match.group(1).split()
        self.assertIn(value, attvalues)

    def test_default_is_en(self):
        response = self.client.get('/')
        self.assert_tag_has_attr(response.content, "html", "lang", "en")
        self.assertEqual(response['Content-Language'], 'en')
        self.assert_tag_has_attr(response.content, "body", "class", "lang_en")

    def test_esperanto(self):
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='eo')
        self.assert_tag_has_attr(response.content, "html", "lang", "eo")
        self.assertEqual(response['Content-Language'], 'eo')
        self.assert_tag_has_attr(response.content, "body", "class", "lang_eo")

    def test_switching_languages_bidi(self):
        response = self.client.get('/')
        self.assert_tag_has_attr(response.content, "html", "lang", "en")
        self.assertEqual(response['Content-Language'], 'en')
        self.assert_tag_has_attr(response.content, "body", "class", "lang_en")
        self.assert_tag_has_attr(response.content, "body", "class", "ltr")

        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='ar')
        self.assert_tag_has_attr(response.content, "html", "lang", "ar")
        self.assertEqual(response['Content-Language'], 'ar')
        self.assert_tag_has_attr(response.content, "body", "class", "lang_ar")
        self.assert_tag_has_attr(response.content, "body", "class", "rtl")
