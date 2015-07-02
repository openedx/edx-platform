"""
Tests of DarkLangMiddleware
"""
from django.contrib.auth.models import User
from django.http import HttpRequest

import ddt
from django.test import TestCase
from mock import Mock
import unittest

from dark_lang.middleware import DarkLangMiddleware
from dark_lang.models import DarkLangConfig
# TODO PLAT-671 Import from Django 1.8
# from django.utils.translation import LANGUAGE_SESSION_KEY
from django_locale.trans_real import LANGUAGE_SESSION_KEY
from student.tests.factories import UserFactory


UNSET = object()


def set_if_set(dct, key, value):
    """
    Sets ``key`` in ``dct`` to ``value``
    unless ``value`` is ``UNSET``
    """
    if value is not UNSET:
        dct[key] = value


@ddt.ddt
class DarkLangMiddlewareTests(TestCase):
    """
    Tests of DarkLangMiddleware
    """
    def setUp(self):
        super(DarkLangMiddlewareTests, self).setUp()
        self.user = User()
        self.user.save()
        DarkLangConfig(
            released_languages='rel',
            changed_by=self.user,
            enabled=True
        ).save()

    def process_request(self, language_session_key=UNSET, accept=UNSET, preview_lang=UNSET, clear_lang=UNSET):
        """
        Build a request and then process it using the ``DarkLangMiddleware``.

        Args:
            language_session_key (str): The language code to set in request.session[LANUGAGE_SESSION_KEY]
            accept (str): The accept header to set in request.META['HTTP_ACCEPT_LANGUAGE']
            preview_lang (str): The value to set in request.GET['preview_lang']
            clear_lang (str): The value to set in request.GET['clear_lang']
        """
        session = {}
        set_if_set(session, LANGUAGE_SESSION_KEY, language_session_key)

        meta = {}
        set_if_set(meta, 'HTTP_ACCEPT_LANGUAGE', accept)

        get = {}
        set_if_set(get, 'preview-lang', preview_lang)
        set_if_set(get, 'clear-lang', clear_lang)

        request = Mock(
            spec=HttpRequest,
            session=session,
            META=meta,
            GET=get,
            user=UserFactory()
        )
        self.assertIsNone(DarkLangMiddleware().process_request(request))
        return request

    def assertAcceptEquals(self, value, request):
        """
        Assert that the HTML_ACCEPT_LANGUAGE header in request
        is equal to value
        """
        self.assertEquals(
            value,
            request.META.get('HTTP_ACCEPT_LANGUAGE', UNSET)
        )

    def test_empty_accept(self):
        self.assertAcceptEquals(UNSET, self.process_request())

    def test_wildcard_accept(self):
        self.assertAcceptEquals('*', self.process_request(accept='*'))

    def test_malformed_accept(self):
        self.assertAcceptEquals('', self.process_request(accept='xxxxxxxxxxxx'))
        self.assertAcceptEquals('', self.process_request(accept='en;q=1.0, es-419:q-0.8'))

    def test_released_accept(self):
        self.assertAcceptEquals(
            'rel;q=1.0',
            self.process_request(accept='rel;q=1.0')
        )

    def test_unreleased_accept(self):
        self.assertAcceptEquals(
            'rel;q=1.0',
            self.process_request(accept='rel;q=1.0, unrel;q=0.5')
        )

    def test_accept_with_syslang(self):
        self.assertAcceptEquals(
            'en;q=1.0, rel;q=0.8',
            self.process_request(accept='en;q=1.0, rel;q=0.8, unrel;q=0.5')
        )

    def test_accept_multiple_released_langs(self):
        DarkLangConfig(
            released_languages=('rel, unrel'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            'rel;q=1.0, unrel;q=0.5',
            self.process_request(accept='rel;q=1.0, unrel;q=0.5')
        )

        self.assertAcceptEquals(
            'rel;q=1.0, unrel;q=0.5',
            self.process_request(accept='rel;q=1.0, notrel;q=0.3, unrel;q=0.5')
        )

        self.assertAcceptEquals(
            'rel;q=1.0, unrel;q=0.5',
            self.process_request(accept='notrel;q=0.3, rel;q=1.0, unrel;q=0.5')
        )

    def test_accept_released_territory(self):
        # We will munge 'rel-ter' to be 'rel', so the 'rel-ter'
        # user will actually receive the released language 'rel'
        # (Otherwise, the user will actually end up getting the server default)
        self.assertAcceptEquals(
            'rel;q=1.0, rel;q=0.5',
            self.process_request(accept='rel-ter;q=1.0, rel;q=0.5')
        )

    def test_accept_mixed_case(self):
        self.assertAcceptEquals(
            'rel;q=1.0, rel;q=0.5',
            self.process_request(accept='rel-TER;q=1.0, REL;q=0.5')
        )

        DarkLangConfig(
            released_languages=('REL-TER'),
            changed_by=self.user,
            enabled=True
        ).save()

        # Since we have only released "rel-ter", the requested code "rel" will
        # fuzzy match to "rel-ter", in addition to "rel-ter" exact matching "rel-ter"
        self.assertAcceptEquals(
            'rel-ter;q=1.0, rel-ter;q=0.5',
            self.process_request(accept='rel-ter;q=1.0, rel;q=0.5')
        )

    @ddt.data(
        ('es;q=1.0, pt;q=0.5', 'es-419;q=1.0'),  # 'es' should get 'es-419', not English
        ('es-AR;q=1.0, pt;q=0.5', 'es-419;q=1.0'),  # 'es-AR' should get 'es-419', not English
    )
    @ddt.unpack
    def test_partial_match_es419(self, accept_header, expected):
        # Release es-419
        DarkLangConfig(
            released_languages=('es-419, en'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            expected,
            self.process_request(accept=accept_header)
        )

    def test_partial_match_esar_es(self):
        # If I release 'es', 'es-AR' should get 'es', not English
        DarkLangConfig(
            released_languages=('es, en'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            'es;q=1.0',
            self.process_request(accept='es-AR;q=1.0, pt;q=0.5')
        )

    @ddt.data(
        # Test condition: If I release 'es-419, es, es-es'...
        ('es;q=1.0, pt;q=0.5', 'es;q=1.0'),          # 1. es should get es
        ('es-419;q=1.0, pt;q=0.5', 'es-419;q=1.0'),  # 2. es-419 should get es-419
        ('es-es;q=1.0, pt;q=0.5', 'es-es;q=1.0'),    # 3. es-es should get es-es
    )
    @ddt.unpack
    def test_exact_match_gets_priority(self, accept_header, expected):
        # Release 'es-419, es, es-es'
        DarkLangConfig(
            released_languages=('es-419, es, es-es'),
            changed_by=self.user,
            enabled=True
        ).save()
        self.assertAcceptEquals(
            expected,
            self.process_request(accept=accept_header)
        )

    @unittest.skip("This won't work until fallback is implemented for LA country codes. See LOC-86")
    @ddt.data(
        'es-AR',  # Argentina
        'es-PY',  # Paraguay
    )
    def test_partial_match_es_la(self, latin_america_code):
        # We need to figure out the best way to implement this. There are a ton of LA country
        # codes that ought to fall back to 'es-419' rather than 'es-es'.
        # http://unstats.un.org/unsd/methods/m49/m49regin.htm#americas
        # If I release 'es, es-419'
        # Latin American codes should get es-419
        DarkLangConfig(
            released_languages=('es, es-419'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            'es-419;q=1.0',
            self.process_request(accept='{};q=1.0, pt;q=0.5'.format(latin_america_code))
        )

    def assertSessionLangEquals(self, value, request):
        """
        Assert that the LANGUAGE_SESSION_KEY set in request.session is equal to value
        """
        self.assertEquals(
            value,
            request.session.get(LANGUAGE_SESSION_KEY, UNSET)
        )

    def test_preview_lang_with_released_language(self):
        # Preview lang should always override selection.
        self.assertSessionLangEquals(
            'rel',
            self.process_request(preview_lang='rel')
        )

        self.assertSessionLangEquals(
            'rel',
            self.process_request(preview_lang='rel', language_session_key='notrel')
        )

    def test_preview_lang_with_dark_language(self):
        self.assertSessionLangEquals(
            'unrel',
            self.process_request(preview_lang='unrel')
        )

        self.assertSessionLangEquals(
            'unrel',
            self.process_request(preview_lang='unrel', language_session_key='notrel')
        )

    def test_clear_lang(self):
        self.assertSessionLangEquals(
            UNSET,
            self.process_request(clear_lang=True)
        )

        self.assertSessionLangEquals(
            UNSET,
            self.process_request(clear_lang=True, language_session_key='rel')
        )

        self.assertSessionLangEquals(
            UNSET,
            self.process_request(clear_lang=True, language_session_key='unrel')
        )

    def test_disabled(self):
        DarkLangConfig(enabled=False, changed_by=self.user).save()

        self.assertAcceptEquals(
            'notrel;q=0.3, rel;q=1.0, unrel;q=0.5',
            self.process_request(accept='notrel;q=0.3, rel;q=1.0, unrel;q=0.5')
        )

        self.assertSessionLangEquals(
            'rel',
            self.process_request(clear_lang=True, language_session_key='rel')
        )

        self.assertSessionLangEquals(
            'unrel',
            self.process_request(clear_lang=True, language_session_key='unrel')
        )

        self.assertSessionLangEquals(
            'rel',
            self.process_request(preview_lang='unrel', language_session_key='rel')
        )

    def test_accept_chinese_language_codes(self):
        DarkLangConfig(
            released_languages=('zh-cn, zh-hk, zh-tw'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            'zh-cn;q=1.0, zh-tw;q=0.5, zh-hk;q=0.3',
            self.process_request(accept='zh-Hans;q=1.0, zh-Hant-TW;q=0.5, zh-HK;q=0.3')
        )
