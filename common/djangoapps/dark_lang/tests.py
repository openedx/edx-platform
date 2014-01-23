"""
Tests of DarkLangMiddleware
"""

from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpRequest, QueryDict

from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock

from dark_lang.middleware import DarkLangMiddleware


UNSET = object()


def set_if_set(dict, key, value):
    """
    Sets ``key`` in ``dict`` to ``value``
    unless ``value`` is ``UNSET``
    """
    if value is not UNSET:
        dict[key] = value


@override_settings(RELEASED_LANGUAGES=('rel'))
class DarkLangMiddlewareTests(TestCase):
    """
    Tests of DarkLangMiddleware
    """
    def process_request(self, django_language=UNSET, accept=UNSET, preview_lang=UNSET, clear_lang=UNSET):
        session = {}
        set_if_set(session, 'django_language', django_language)

        META = {}
        set_if_set(META, 'HTTP_ACCEPT_LANGUAGE', accept)

        GET = {}
        set_if_set(GET, 'preview-lang', preview_lang)
        set_if_set(GET, 'clear-lang', clear_lang)

        request = Mock(
            spec=HttpRequest,
            session=session,
            META=META,
            GET=GET
        )
        self.assertIsNone(DarkLangMiddleware().process_request(request))
        return request

    @override_settings(RELEASED_LANGUAGES=None)
    def test_inactive_middleware(self):
        with self.assertRaises(MiddlewareNotUsed):
            DarkLangMiddleware()

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

    @override_settings(RELEASED_LANGUAGES=('rel', 'unrel'))
    def test_accept_multiple_released_langs(self):

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

