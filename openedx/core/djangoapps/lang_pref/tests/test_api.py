# -*- coding: utf-8 -*-
""" Tests for the language API. """

from mock import patch
from django.test.utils import override_settings
from django.utils import translation
from django.contrib.auth.models import User
import ddt

from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref import api as language_api
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase

EN = language_api.Language('en', 'English')
AR = language_api.Language('ar', 'Arabic')
ES_419 = language_api.Language('es-419', u'Español (Latinoamérica)')


@ddt.ddt
class LanguageApiTest(CacheIsolationTestCase):
    """
    Tests of the language APIs.
    """

    @ddt.data(
        # Should return the base config value
        ({'SHOW_HEADER_LANGUAGE_SELECTOR': True}, {}, True),

        # Should return the site config value
        ({'SHOW_HEADER_LANGUAGE_SELECTOR': False}, {'SHOW_HEADER_LANGUAGE_SELECTOR': True}, True),
        ({'SHOW_HEADER_LANGUAGE_SELECTOR': True}, {'SHOW_HEADER_LANGUAGE_SELECTOR': False}, False),

        # SHOW_LANGUAGE_SELECTOR should supercede SHOW_HEADER_LANGUAGE_SELECTOR when true
        ({'SHOW_HEADER_LANGUAGE_SELECTOR': False, 'SHOW_LANGUAGE_SELECTOR': True}, {}, True),
        ({'SHOW_HEADER_LANGUAGE_SELECTOR': False}, {'SHOW_LANGUAGE_SELECTOR': True}, True)
    )
    @ddt.unpack
    def test_header_language_selector_is_enabled(self, base_config, site_config, expected):
        """
        Verify that the header language selector config is correct.
        """
        with patch.dict('django.conf.settings.FEATURES', base_config):
            with with_site_configuration_context(configuration=site_config):
                self.assertEqual(language_api.header_language_selector_is_enabled(), expected)

    @ddt.data(
        # Should return the base config value
        ({'SHOW_FOOTER_LANGUAGE_SELECTOR': True}, {}, True),

        # Should return the site config value
        ({'SHOW_FOOTER_LANGUAGE_SELECTOR': False}, {'SHOW_FOOTER_LANGUAGE_SELECTOR': True}, True),
        ({'SHOW_FOOTER_LANGUAGE_SELECTOR': True}, {'SHOW_FOOTER_LANGUAGE_SELECTOR': False}, False)
    )
    @ddt.unpack
    def test_footer_language_selector_is_enabled(self, base_config, site_config, expected):
        """
        Verify that the footer language selector config is correct.
        """
        with patch.dict('django.conf.settings.FEATURES', base_config):
            with with_site_configuration_context(configuration=site_config):
                self.assertEqual(language_api.footer_language_selector_is_enabled(), expected)

    @ddt.data(*[
        ('en', [], [], []),
        ('en', [EN], [], [EN]),
        ('en', [EN, ES_419], [], [EN]),
        ('en', [EN, ES_419], ['es-419'], [EN, ES_419]),
        ('es-419', [EN, ES_419], ['es-419'], [ES_419]),
        ('en', [EN, ES_419], ['es'], [EN]),
    ])
    @ddt.unpack
    def test_released_languages(self, default_lang, languages, dark_lang_released, expected_languages):
        """
        Tests for the released languages.
        """
        with override_settings(LANGUAGES=languages, LANGUAGE_CODE=default_lang):
            user = User()
            user.save()
            DarkLangConfig(
                released_languages=', '.join(dark_lang_released),
                changed_by=user,
                enabled=True
            ).save()
            released_languages = language_api.released_languages()
            self.assertEqual(released_languages, expected_languages)

    @ddt.data(*[
        (True, 'en', [], [], [], []),
        (True, 'en', [EN], [], [], [EN]),
        (True, 'en', [EN, ES_419], [], [], [EN]),
        (True, 'en', [EN, ES_419], ['es-419'], ['ar'], [EN, ES_419, AR]),
        (False, 'en', [EN, ES_419], ['es-419'], ['ar'], [EN, ES_419]),
        (True, 'es-419', [EN, ES_419], ['es-419'], ['ar'], [ES_419, AR]),
        (True, 'en', [EN, ES_419], ['es'], [], [EN]),
    ])
    @ddt.unpack
    def test_released_beta_languages(
            self, enable_beta_languages, default_lang, languages, dark_lang_released, beta_languages, expected_languages
    ):
        """
        Tests for the released languages.
        """
        with override_settings(LANGUAGES=languages, LANGUAGE_CODE=default_lang):
            user = User()
            user.save()
            DarkLangConfig(
                released_languages=', '.join(dark_lang_released),
                beta_languages=', '.join(beta_languages),
                changed_by=user,
                enabled=True,
                enable_beta_languages=enable_beta_languages
            ).save()
            released_languages = language_api.released_languages()
            self.assertEqual(released_languages, expected_languages)

    @ddt.data(*[
        (True, [], []),
        (True, ['es-419'], [ES_419]),
        (False, ['es-419'], [])
    ])
    def test_beta_languages(self, enable_beta_languages, beta_languages, expected_languages):
        """
        Test for beta languages 
        """
        user = User()
        user.save()
        DarkLangConfig(
            released_languages='en',
            enable_beta_languages=enable_beta_languages,
            beta_languages=', '.join(beta_languages),
            changed_by=user,
            enabled=True
        ).save()
        beta_languages = language_api.beta_languages()
        self.assertEqual(beta_languages, expected_languages)

    @override_settings(ALL_LANGUAGES=[[u"cs", u"Czech"], [u"nl", u"Dutch"]])
    def test_all_languages(self):
        """
        Tests for the list of all languages.
        """
        with translation.override('fr'):
            all_languages = language_api.all_languages()

        self.assertEqual(2, len(all_languages))
        self.assertLess(all_languages[0][1], all_languages[1][1])
        self.assertEqual("nl", all_languages[0][0])
        self.assertEqual("cs", all_languages[1][0])
        self.assertEqual(u"Hollandais", all_languages[0][1])
        self.assertEqual(u"Tchèque", all_languages[1][1])
