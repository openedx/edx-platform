"""
Tests of DarkLangMiddleware
"""
from django.contrib.auth.models import User
from django.http import HttpRequest

from django.test import TestCase
from mock import Mock

from dark_lang.middleware import DarkLangMiddleware
from dark_lang.models import DarkLangConfig


UNSET = object()


def set_if_set(dct, key, value):
    """
    Sets ``key`` in ``dct`` to ``value``
    unless ``value`` is ``UNSET``
    """
    if value is not UNSET:
        dct[key] = value


class DarkLangMiddlewareTests(TestCase):
    """
    Tests of DarkLangMiddleware
    """
    def setUp(self):
        self.user = User()
        self.user.save()
        DarkLangConfig(
            released_languages='rel',
            changed_by=self.user,
            enabled=True
        ).save()

    def process_request(self, django_language=UNSET, accept=UNSET, preview_lang=UNSET, clear_lang=UNSET):
        """
        Build a request and then process it using the ``DarkLangMiddleware``.

        Args:
            django_language (str): The language code to set in request.session['django_language']
            accept (str): The accept header to set in request.META['HTTP_ACCEPT_LANGUAGE']
            preview_lang (str): The value to set in request.GET['preview_lang']
            clear_lang (str): The value to set in request.GET['clear_lang']
        """
        session = {}
        set_if_set(session, 'django_language', django_language)

        meta = {}
        set_if_set(meta, 'HTTP_ACCEPT_LANGUAGE', accept)

        get = {}
        set_if_set(get, 'preview-lang', preview_lang)
        set_if_set(get, 'clear-lang', clear_lang)

        request = Mock(
            spec=HttpRequest,
            session=session,
            META=meta,
            GET=get
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
        self.assertAcceptEquals(
            'rel-ter;q=1.0, rel;q=0.5',
            self.process_request(accept='rel-ter;q=1.0, rel;q=0.5')
        )

    def test_accept_mixed_case(self):
        self.assertAcceptEquals(
            'rel-TER;q=1.0, REL;q=0.5',
            self.process_request(accept='rel-TER;q=1.0, REL;q=0.5')
        )

        DarkLangConfig(
            released_languages=('REL-TER'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            'rel-ter;q=1.0',
            self.process_request(accept='rel-ter;q=1.0, rel;q=0.5')
        )


    def assertSessionLangEquals(self, value, request):
        """
        Assert that the 'django_language' set in request.session is equal to value
        """
        self.assertEquals(
            value,
            request.session.get('django_language', UNSET)
        )

    def test_preview_lang_with_released_language(self):
        self.assertSessionLangEquals(
            UNSET,
            self.process_request(preview_lang='rel')
        )

        self.assertSessionLangEquals(
            'notrel',
            self.process_request(preview_lang='rel', django_language='notrel')
        )

    def test_preview_lang_with_dark_language(self):
        self.assertSessionLangEquals(
            'unrel',
            self.process_request(preview_lang='unrel')
        )

        self.assertSessionLangEquals(
            'unrel',
            self.process_request(preview_lang='unrel', django_language='notrel')
        )

    def test_clear_lang(self):
        self.assertSessionLangEquals(
            UNSET,
            self.process_request(clear_lang=True)
        )

        self.assertSessionLangEquals(
            UNSET,
            self.process_request(clear_lang=True, django_language='rel')
        )

        self.assertSessionLangEquals(
            UNSET,
            self.process_request(clear_lang=True, django_language='unrel')
        )

    def test_disabled(self):
        DarkLangConfig(enabled=False, changed_by=self.user).save()

        self.assertAcceptEquals(
            'notrel;q=0.3, rel;q=1.0, unrel;q=0.5',
            self.process_request(accept='notrel;q=0.3, rel;q=1.0, unrel;q=0.5')
        )

        self.assertSessionLangEquals(
            'rel',
            self.process_request(clear_lang=True, django_language='rel')
        )

        self.assertSessionLangEquals(
            'unrel',
            self.process_request(clear_lang=True, django_language='unrel')
        )

        self.assertSessionLangEquals(
            'rel',
            self.process_request(preview_lang='unrel', django_language='rel')
        )

    def test_accept_chinese_language_codes(self):
        DarkLangConfig(
            released_languages=('zh-cn, zh-hk, zh-tw'),
            changed_by=self.user,
            enabled=True
        ).save()

        self.assertAcceptEquals(
            'zh-CN;q=1.0, zh-TW;q=0.5, zh-HK;q=0.3',
            self.process_request(accept='zh-Hans;q=1.0, zh-Hant-TW;q=0.5, zh-HK;q=0.3')
        )
