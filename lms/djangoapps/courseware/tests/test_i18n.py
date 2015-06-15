"""
Tests i18n in courseware
"""
import re
from nose.plugins.attrib import attr

from django.contrib.auth.models import User
from django.test import TestCase

from dark_lang.models import DarkLangConfig


class BaseI18nTestCase(TestCase):
    """
    Base utilities for i18n test classes to derive from
    """
    def assert_tag_has_attr(self, content, tag, attname, value):
        """Assert that a tag in `content` has a certain value in a certain attribute."""
        regex = r"""<{tag} [^>]*\b{attname}=['"]([\w\d\- ]+)['"][^>]*>""".format(tag=tag, attname=attname)
        match = re.search(regex, content)
        self.assertTrue(match, "Couldn't find desired tag '%s' with attr '%s' in %r" % (tag, attname, content))
        attvalues = match.group(1).split()
        self.assertIn(value, attvalues)

    def release_languages(self, languages):
        """
        Release a set of languages using the dark lang interface.
        languages is a list of comma-separated lang codes, eg, 'ar, es-419'
        """
        user = User()
        user.save()
        DarkLangConfig(
            released_languages=languages,
            changed_by=user,
            enabled=True
        ).save()


@attr('shard_1')
class I18nTestCase(BaseI18nTestCase):
    """
    Tests for i18n
    """
    def test_default_is_en(self):
        self.release_languages('fr')
        response = self.client.get('/')
        self.assert_tag_has_attr(response.content, "html", "lang", "en")
        self.assertEqual(response['Content-Language'], 'en')
        self.assert_tag_has_attr(response.content, "body", "class", "lang_en")

    def test_esperanto(self):
        self.release_languages('fr, eo')
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='eo')
        self.assert_tag_has_attr(response.content, "html", "lang", "eo")
        self.assertEqual(response['Content-Language'], 'eo')
        self.assert_tag_has_attr(response.content, "body", "class", "lang_eo")

    def test_switching_languages_bidi(self):
        self.release_languages('ar, eo')
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


@attr('shard_1')
class I18nRegressionTests(BaseI18nTestCase):
    """
    Tests for i18n
    """
    def test_es419_acceptance(self):
        # Regression test; LOC-72, and an issue with Django
        self.release_languages('es-419')
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='es-419')
        self.assert_tag_has_attr(response.content, "html", "lang", "es-419")

    def test_unreleased_lang_resolution(self):
        # Regression test; LOC-85
        self.release_languages('fa')

        # We've released 'fa', AND we have language files for 'fa-ir' but
        # we want to keep 'fa-ir' as a dark language. Requesting 'fa-ir'
        # in the http request (NOT with the ?preview-lang query param) should
        # receive files for 'fa'
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='fa-ir')
        self.assert_tag_has_attr(response.content, "html", "lang", "fa")
