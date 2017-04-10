# -*- coding: utf-8 -*-
""" Tests for the language API. """

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import translation
from django.contrib.auth.models import User
import ddt

from openedx.core.djangoapps.dark_lang.models import DarkLangConfig

from openedx.core.djangoapps.lang_pref import api as language_api

EN = language_api.Language('en', 'English')
ES_419 = language_api.Language('es-419', u'Español (Latinoamérica)')


@ddt.ddt
class LanguageApiTest(TestCase):
    """
    Tests of the language APIs.
    """
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
