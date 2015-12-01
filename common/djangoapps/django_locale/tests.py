# pylint: disable=invalid-name, line-too-long, super-method-not-called
"""
Tests taken from Django upstream:
https://github.com/django/django/blob/e6b34193c5c7d117ededdab04bb16caf8864f07c/tests/regressiontests/i18n/tests.py
"""
from django.conf import settings
from django.test import TestCase, RequestFactory
from django_locale.trans_real import (
    parse_accept_lang_header, get_language_from_request, LANGUAGE_SESSION_KEY
)

# Added to test middleware around dark lang
from django.contrib.auth.models import User
from django.test.utils import override_settings
from dark_lang.models import DarkLangConfig


# Adding to support test differences between Django and our own settings
@override_settings(LANGUAGES=[
    ('pt', 'Portuguese'),
    ('pt-br', 'Portuguese-Brasil'),
    ('es', 'Spanish'),
    ('es-ar', 'Spanish (Argentina)'),
    ('de', 'Deutch'),
    ('zh-cn', 'Chinese (China)'),
    ('ar-sa', 'Arabic (Saudi Arabia)'),
])
class MiscTests(TestCase):
    """
    Tests taken from Django upstream:
    https://github.com/django/django/blob/e6b34193c5c7d117ededdab04bb16caf8864f07c/tests/regressiontests/i18n/tests.py
    """
    def setUp(self):
        self.rf = RequestFactory()
        # Added to test middleware around dark lang
        user = User()
        user.save()
        DarkLangConfig(
            released_languages='pt, pt-br, es, de, es-ar, zh-cn, ar-sa',
            changed_by=user,
            enabled=True
        ).save()

    def test_parse_spec_http_header(self):
        """
        Testing HTTP header parsing. First, we test that we can parse the
        values according to the spec (and that we extract all the pieces in
        the right order).
        """
        p = parse_accept_lang_header
        # Good headers.
        self.assertEqual([('de', 1.0)], p('de'))
        self.assertEqual([('en-AU', 1.0)], p('en-AU'))
        self.assertEqual([('es-419', 1.0)], p('es-419'))
        self.assertEqual([('*', 1.0)], p('*;q=1.00'))
        self.assertEqual([('en-AU', 0.123)], p('en-AU;q=0.123'))
        self.assertEqual([('en-au', 0.5)], p('en-au;q=0.5'))
        self.assertEqual([('en-au', 1.0)], p('en-au;q=1.0'))
        self.assertEqual([('da', 1.0), ('en', 0.5), ('en-gb', 0.25)], p('da, en-gb;q=0.25, en;q=0.5'))
        self.assertEqual([('en-au-xx', 1.0)], p('en-au-xx'))
        self.assertEqual([('de', 1.0), ('en-au', 0.75), ('en-us', 0.5), ('en', 0.25), ('es', 0.125), ('fa', 0.125)], p('de,en-au;q=0.75,en-us;q=0.5,en;q=0.25,es;q=0.125,fa;q=0.125'))
        self.assertEqual([('*', 1.0)], p('*'))
        self.assertEqual([('de', 1.0)], p('de;q=0.'))
        self.assertEqual([('en', 1.0), ('*', 0.5)], p('en; q=1.0, * ; q=0.5'))
        self.assertEqual([], p(''))

        # Bad headers; should always return [].
        self.assertEqual([], p('en-gb;q=1.0000'))
        self.assertEqual([], p('en;q=0.1234'))
        self.assertEqual([], p('en;q=.2'))
        self.assertEqual([], p('abcdefghi-au'))
        self.assertEqual([], p('**'))
        self.assertEqual([], p('en,,gb'))
        self.assertEqual([], p('en-au;q=0.1.0'))
        self.assertEqual([], p('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXZ,en'))
        self.assertEqual([], p('da, en-gb;q=0.8, en;q=0.7,#'))
        self.assertEqual([], p('de;q=2.0'))
        self.assertEqual([], p('de;q=0.a'))
        self.assertEqual([], p('12-345'))
        self.assertEqual([], p(''))

    def test_parse_literal_http_header(self):
        """
        Now test that we parse a literal HTTP header correctly.
        """
        g = get_language_from_request
        r = self.rf.get('/')
        r.COOKIES = {}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'pt-br'}
        self.assertEqual('pt-br', g(r))

        r.META = {'HTTP_ACCEPT_LANGUAGE': 'pt'}
        self.assertEqual('pt', g(r))

        r.META = {'HTTP_ACCEPT_LANGUAGE': 'es,de'}
        self.assertEqual('es', g(r))

        r.META = {'HTTP_ACCEPT_LANGUAGE': 'es-ar,de'}
        self.assertEqual('es-ar', g(r))

        # This test assumes there won't be a Django translation to a US
        # variation of the Spanish language, a safe assumption. When the
        # user sets it as the preferred language, the main 'es'
        # translation should be selected instead.
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'es-us'}
        self.assertEqual(g(r), 'es')

        # This tests the following scenario: there isn't a main language (zh)
        # translation of Django but there is a translation to variation (zh_CN)
        # the user sets zh-cn as the preferred language, it should be selected
        # by Django without falling back nor ignoring it.
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'zh-cn,de'}
        self.assertEqual(g(r), 'zh-cn')

    def test_logic_masked_by_darklang(self):
        g = get_language_from_request
        r = self.rf.get('/')
        r.COOKIES = {}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'ar-qa'}
        self.assertEqual('ar-sa', g(r))

        r.session = {LANGUAGE_SESSION_KEY: 'es'}
        self.assertEqual('es', g(r))

    def test_parse_language_cookie(self):
        """
        Now test that we parse language preferences stored in a cookie correctly.
        """
        g = get_language_from_request
        r = self.rf.get('/')
        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'pt-br'}
        r.META = {}
        self.assertEqual('pt-br', g(r))

        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'pt'}
        r.META = {}
        self.assertEqual('pt', g(r))

        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'es'}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'de'}
        self.assertEqual('es', g(r))

        # This test assumes there won't be a Django translation to a US
        # variation of the Spanish language, a safe assumption. When the
        # user sets it as the preferred language, the main 'es'
        # translation should be selected instead.
        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'es-us'}
        r.META = {}
        self.assertEqual(g(r), 'es')

        # This tests the following scenario: there isn't a main language (zh)
        # translation of Django but there is a translation to variation (zh_CN)
        # the user sets zh-cn as the preferred language, it should be selected
        # by Django without falling back nor ignoring it.
        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'zh-cn'}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'de'}
        self.assertEqual(g(r), 'zh-cn')
