# -*- coding: utf-8 -*-
""" Tests for the language API. """


import ddt
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.utils import translation
from mock import patch
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref import api as language_api
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase

EN = language_api.Language('en', 'English')
ES_419 = language_api.Language('es-419', u'Español (Latinoamérica)')
LT_LT = language_api.Language('lt-lt', u'Lietuvių (Lietuva)')


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

    def test_beta_languages(self):
        """
        Tests for the beta languages.
        """
        with override_settings(LANGUAGES=[EN, ES_419, LT_LT], LANGUAGE_CODE='en'):
            user = User()
            user.save()
            DarkLangConfig(
                released_languages='es-419',
                changed_by=user,
                enabled=True,
                beta_languages='lt-lt',
                enable_beta_languages=True
            ).save()

            released_languages = language_api.released_languages()
            expected_languages = [EN, ES_419, LT_LT]
            self.assertEqual(released_languages, expected_languages)
