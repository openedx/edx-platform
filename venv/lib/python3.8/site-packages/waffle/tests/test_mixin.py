from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory

from test_app import views
from waffle.middleware import WaffleMiddleware
from waffle.models import Flag, Sample, Switch
from waffle.tests.base import TestCase


def get(**kw):
    request = RequestFactory().get('/foo', data=kw)
    request.user = AnonymousUser()
    return request


def process_request(request, view):
    response = view.as_view()(request)
    return WaffleMiddleware().process_response(request, response)


class WaffleFlagMixinTest(TestCase):
    def setUp(self):
        self.request = get()

    def test_flag_must_be_active(self):
        view = views.FlagView
        self.assertRaises(Http404, process_request, self.request, view)

        Flag.objects.create(name='foo', everyone=True)
        response = process_request(self.request, view)
        self.assertEqual(b'foo', response.content)

    def test_flag_must_be_inactive(self):
        view = views.FlagOffView
        response = process_request(self.request, view)
        self.assertEqual(b'foo', response.content)

        Flag.objects.create(name='foo', everyone=True)
        self.assertRaises(Http404, process_request, self.request, view)

    def test_override_with_cookie(self):
        Flag.objects.create(name='foo', percent='0.1')
        self.request.COOKIES['dwf_foo'] = 'True'
        response = process_request(self.request, views.FlagView)
        self.assertEqual(b'foo', response.content)
        self.assertIn('dwf_foo', response.cookies)
        self.assertEqual('True', response.cookies['dwf_foo'].value)


class WaffleSampleMixinTest(TestCase):
    def setUp(self):
        self.request = get()

    def test_sample_must_be_active(self):
        view = views.SampleView
        self.assertRaises(Http404, process_request, self.request, view)

        Sample.objects.create(name='foo', percent='100.0')
        response = process_request(self.request, view)
        self.assertEqual(b'foo', response.content)

    def test_sample_must_be_inactive(self):
        view = views.SampleOffView
        response = process_request(self.request, view)
        self.assertEqual(b'foo', response.content)

        Sample.objects.create(name='foo', percent='100.0')
        self.assertRaises(Http404, process_request, self.request, view)

    def test_override_with_cookie(self):
        Sample.objects.create(name='foo', percent='0.0')
        self.request.COOKIES['dwf_foo'] = 'True'
        self.assertRaises(Http404, process_request, self.request,
                          views.SwitchView)


class WaffleSwitchMixinTest(TestCase):
    def setUp(self):
        self.request = get()

    def test_switch_must_be_active(self):
        view = views.SwitchView
        self.assertRaises(Http404, process_request, self.request, view)

        Switch.objects.create(name='foo', active=True)
        response = process_request(self.request, view)
        self.assertEqual(b'foo', response.content)

    def test_switch_must_be_inactive(self):
        view = views.SwitchOffView
        response = process_request(self.request, view)
        self.assertEqual(b'foo', response.content)

        Switch.objects.create(name='foo', active=True)
        self.assertRaises(Http404, process_request, self.request, view)

    def test_no_override_with_cookie(self):
        Switch.objects.create(name='foo', active=False)
        self.request.COOKIES['dwf_foo'] = 'True'
        self.assertRaises(Http404, process_request, self.request,
                          views.SwitchView)
