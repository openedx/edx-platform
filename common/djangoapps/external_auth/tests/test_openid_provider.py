#-*- encoding=utf-8 -*-
'''
Created on Jan 18, 2013

@author: brian
'''
import openid
from openid.fetchers import HTTPFetcher, HTTPResponse
from urlparse import parse_qs, urlparse

from django.conf import settings
from django.test import TestCase, LiveServerTestCase
from django.core.cache import cache
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from unittest import skipUnless

from student.tests.factories import UserFactory
from external_auth.views import provider_login


class MyFetcher(HTTPFetcher):
    """A fetcher that uses server-internal calls for performing HTTP
    requests.
    """

    def __init__(self, client):
        """@param client: A test client object"""

        super(MyFetcher, self).__init__()
        self.client = client

    def fetch(self, url, body=None, headers=None):
        """Perform an HTTP request

        @raises Exception: Any exception that can be raised by Django

        @see: C{L{HTTPFetcher.fetch}}
        """
        if body:
            # method = 'POST'
            # undo the URL encoding of the POST arguments
            data = parse_qs(body)
            response = self.client.post(url, data)
        else:
            # method = 'GET'
            data = {}
            if headers and 'Accept' in headers:
                data['CONTENT_TYPE'] = headers['Accept']
            response = self.client.get(url, data)

        # Translate the test client response to the fetcher's HTTP response abstraction
        content = response.content
        final_url = url
        response_headers = {}
        if 'Content-Type' in response:
            response_headers['content-type'] = response['Content-Type']
        if 'X-XRDS-Location' in response:
            response_headers['x-xrds-location'] = response['X-XRDS-Location']
        status = response.status_code

        return HTTPResponse(
            body=content,
            final_url=final_url,
            headers=response_headers,
            status=status,
        )


class OpenIdProviderTest(TestCase):
    """
    Tests of the OpenId login
    """
    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_begin_login_with_xrds_url(self):

        # the provider URL must be converted to an absolute URL in order to be
        # used as an openid provider.
        provider_url = reverse('openid-provider-xrds')
        factory = RequestFactory()
        request = factory.request()
        abs_provider_url = request.build_absolute_uri(location=provider_url)

        # In order for this absolute URL to work (i.e. to get xrds, then authentication)
        # in the test environment, we either need a live server that works with the default
        # fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
        # Here we do the latter:
        fetcher = MyFetcher(self.client)
        openid.fetchers.setDefaultFetcher(fetcher, wrap_exceptions=False)

        # now we can begin the login process by invoking a local openid client,
        # with a pointer to the (also-local) openid provider:
        with self.settings(OPENID_SSO_SERVER_URL=abs_provider_url):

            url = reverse('openid-login')
            resp = self.client.post(url)
            code = 200
            self.assertEqual(resp.status_code, code,
                             "got code {0} for url '{1}'. Expected code {2}"
                             .format(resp.status_code, url, code))

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_begin_login_with_login_url(self):

        # the provider URL must be converted to an absolute URL in order to be
        # used as an openid provider.
        provider_url = reverse('openid-provider-login')
        factory = RequestFactory()
        request = factory.request()
        abs_provider_url = request.build_absolute_uri(location=provider_url)

        # In order for this absolute URL to work (i.e. to get xrds, then authentication)
        # in the test environment, we either need a live server that works with the default
        # fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
        # Here we do the latter:
        fetcher = MyFetcher(self.client)
        openid.fetchers.setDefaultFetcher(fetcher, wrap_exceptions=False)

        # now we can begin the login process by invoking a local openid client,
        # with a pointer to the (also-local) openid provider:
        with self.settings(OPENID_SSO_SERVER_URL=abs_provider_url):
            url = reverse('openid-login')
            resp = self.client.post(url)
            code = 200
            self.assertEqual(resp.status_code, code,
                             "got code {0} for url '{1}'. Expected code {2}"
                             .format(resp.status_code, url, code))
            self.assertContains(resp, '<input name="openid.mode" type="hidden" value="checkid_setup" />', html=True)
            self.assertContains(resp, '<input name="openid.ns" type="hidden" value="http://specs.openid.net/auth/2.0" />', html=True)
            self.assertContains(resp, '<input name="openid.identity" type="hidden" value="http://specs.openid.net/auth/2.0/identifier_select" />', html=True)
            self.assertContains(resp, '<input name="openid.claimed_id" type="hidden" value="http://specs.openid.net/auth/2.0/identifier_select" />', html=True)
            self.assertContains(resp, '<input name="openid.ns.ax" type="hidden" value="http://openid.net/srv/ax/1.0" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.mode" type="hidden" value="fetch_request" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.required" type="hidden" value="email,fullname,old_email,firstname,old_nickname,lastname,old_fullname,nickname" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.fullname" type="hidden" value="http://axschema.org/namePerson" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.lastname" type="hidden" value="http://axschema.org/namePerson/last" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.firstname" type="hidden" value="http://axschema.org/namePerson/first" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.nickname" type="hidden" value="http://axschema.org/namePerson/friendly" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.email" type="hidden" value="http://axschema.org/contact/email" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.old_email" type="hidden" value="http://schema.openid.net/contact/email" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.old_nickname" type="hidden" value="http://schema.openid.net/namePerson/friendly" />', html=True)
            self.assertContains(resp, '<input name="openid.ax.type.old_fullname" type="hidden" value="http://schema.openid.net/namePerson" />', html=True)
            self.assertContains(resp, '<input type="submit" value="Continue" />', html=True)
            # this should work on the server:
            self.assertContains(resp, '<input name="openid.realm" type="hidden" value="http://testserver/" />', html=True)

            # not included here are elements that will vary from run to run:
            # <input name="openid.return_to" type="hidden" value="http://testserver/openid/complete/?janrain_nonce=2013-01-23T06%3A20%3A17ZaN7j6H" />
            # <input name="openid.assoc_handle" type="hidden" value="{HMAC-SHA1}{50ff8120}{rh87+Q==}" />

    def attempt_login(self, expected_code, login_method='POST', **kwargs):
        """ Attempt to log in through the open id provider login """
        url = reverse('openid-provider-login')
        args = {
            "openid.mode": "checkid_setup",
            "openid.return_to": "http://testserver/openid/complete/?janrain_nonce=2013-01-23T06%3A20%3A17ZaN7j6H",
            "openid.assoc_handle": "{HMAC-SHA1}{50ff8120}{rh87+Q==}",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.realm": "http://testserver/",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.ns.ax": "http://openid.net/srv/ax/1.0",
            "openid.ax.mode": "fetch_request",
            "openid.ax.required": "email,fullname,old_email,firstname,old_nickname,lastname,old_fullname,nickname",
            "openid.ax.type.fullname": "http://axschema.org/namePerson",
            "openid.ax.type.lastname": "http://axschema.org/namePerson/last",
            "openid.ax.type.firstname": "http://axschema.org/namePerson/first",
            "openid.ax.type.nickname": "http://axschema.org/namePerson/friendly",
            "openid.ax.type.email": "http://axschema.org/contact/email",
            "openid.ax.type.old_email": "http://schema.openid.net/contact/email",
            "openid.ax.type.old_nickname": "http://schema.openid.net/namePerson/friendly",
            "openid.ax.type.old_fullname": "http://schema.openid.net/namePerson",
        }
        # override the default args with any given arguments
        for key in kwargs:
            args["openid." + key] = kwargs[key]

        if login_method == 'POST':
            resp = self.client.post(url, args)
        elif login_method == 'GET':
            resp = self.client.get(url, args)
        else:
            self.fail('Invalid login method')

        code = expected_code
        self.assertEqual(resp.status_code, code,
                         "got code {0} for url '{1}'. Expected code {2}"
                         .format(resp.status_code, url, code))

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_open_id_setup(self):
        """ Attempt a standard successful login """
        self.attempt_login(200)

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_invalid_namespace(self):
        """ Test for 403 error code when the namespace of the request is invalid"""
        self.attempt_login(403, ns="http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")

    @override_settings(OPENID_PROVIDER_TRUSTED_ROOTS=['http://apps.cs50.edx.org'])
    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_invalid_return_url(self):
        """ Test for 403 error code when the url"""
        self.attempt_login(403, return_to="http://apps.cs50.edx.or")

    def _send_bad_redirection_login(self):
        """
        Attempt to log in to the provider with setup parameters

        Intentionally fail the login to force a redirect
        """
        user = UserFactory()

        factory = RequestFactory()
        post_params = {'email': user.email, 'password': 'password'}
        fake_url = 'fake url'
        request = factory.post(reverse('openid-provider-login'), post_params)
        openid_setup = {
            'request': factory.request(),
            'url': fake_url,
            'post_params': {}
        }
        request.session = {
            'openid_setup': openid_setup
        }
        response = provider_login(request)
        return response

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_login_openid_handle_redirection(self):
        """ Test to see that we can handle login redirection properly"""
        response = self._send_bad_redirection_login()
        self.assertEquals(response.status_code, 302)

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_login_openid_handle_redirection_ratelimited(self):
        # try logging in 30 times, the default limit in the number of failed
        # log in attempts before the rate gets limited
        for _ in xrange(30):
            self._send_bad_redirection_login()

        response = self._send_bad_redirection_login()
        # verify that we are not returning the default 403
        self.assertEquals(response.status_code, 302)
        # clear the ratelimit cache so that we don't fail other logins
        cache.clear()

    def _attempt_login_and_perform_final_response(self, user, profile_name):
        """
        Performs full procedure of a successful OpenID provider login for user,
        all required data is taken form ``user`` attribute which is an instance
        of ``User`` model. As a convenience this method will also set
        ``profile.name`` for the user.
        """
        url = reverse('openid-provider-login')

        # login to the client so that we can persist session information
        user.profile.name = profile_name
        user.profile.save()
        # It is asssumed that user's password is test (default for UserFactory)
        self.client.login(username=user.username, password='test')
        # login once to get the right session information
        self.attempt_login(200)
        post_args = {
            'email': user.email,
            'password': 'test'
        }

        # call url again, this time with username and password
        return self.client.post(url, post_args)

    @skipUnless(
        settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'), 'OpenID not enabled')
    def test_provider_login_can_handle_unicode_email(self):
        user = UserFactory(email=u"user.ąęł@gmail.com")
        resp = self._attempt_login_and_perform_final_response(user, u"Jan ĄĘŁ")
        location = resp['Location']
        parsed_url = urlparse(location)
        parsed_qs = parse_qs(parsed_url.query)
        self.assertEquals(parsed_qs['openid.ax.type.ext1'][0], 'http://axschema.org/contact/email')
        self.assertEquals(parsed_qs['openid.ax.type.ext0'][0], 'http://axschema.org/namePerson')
        self.assertEquals(parsed_qs['openid.ax.value.ext0.1'][0],
                          user.profile.name.encode('utf-8'))  # pylint: disable=no-member
        self.assertEquals(parsed_qs['openid.ax.value.ext1.1'][0],
                          user.email.encode('utf-8'))  # pylint: disable=no-member

    @skipUnless(
        settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'), 'OpenID not enabled')
    def test_provider_login_can_handle_unicode_email_invalid_password(self):
        user = UserFactory(email=u"user.ąęł@gmail.com")
        url = reverse('openid-provider-login')

        # login to the client so that we can persist session information
        user.profile.name = u"Jan ĄĘ"
        user.profile.save()
        # It is asssumed that user's password is test (default for UserFactory)
        self.client.login(username=user.username, password='test')
        # login once to get the right session information
        self.attempt_login(200)
        # We trigger situation where user password is invalid at last phase
        # of openid login
        post_args = {
            'email': user.email,
            'password': 'invalid-password'
        }

        # call url again, this time with username and password
        return self.client.post(url, post_args)

    @skipUnless(
        settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'), 'OpenID not enabled')
    def test_provider_login_can_handle_unicode_email_inactive_account(self):
        user = UserFactory(email=u"user.ąęł@gmail.com", username=u"ąęół")
        url = reverse('openid-provider-login')

        # login to the client so that we can persist session information
        user.profile.name = u'Jan ĄĘ'
        user.profile.save()  # pylint: disable=no-member
        self.client.login(username=user.username, password='test')
        # login once to get the right session information
        self.attempt_login(200)
        # We trigger situation where user is not active at final phase of
        # OpenId login.
        user.is_active = False
        user.save()  # pylint: disable=no-member
        post_args = {
            'email': user.email,
            'password': 'test'
        }
        # call url again, this time with username and password
        self.client.post(url, post_args)

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_openid_final_response(self):

        user = UserFactory()

        # login to the client so that we can persist session information
        for name in ['Robot 33', '☃']:
            resp = self._attempt_login_and_perform_final_response(user, name)
            # all information is embedded in the redirect url
            location = resp['Location']
            # parse the url
            parsed_url = urlparse(location)
            parsed_qs = parse_qs(parsed_url.query)
            self.assertEquals(parsed_qs['openid.ax.type.ext1'][0], 'http://axschema.org/contact/email')
            self.assertEquals(parsed_qs['openid.ax.type.ext0'][0], 'http://axschema.org/namePerson')
            self.assertEquals(parsed_qs['openid.ax.value.ext1.1'][0], user.email)
            self.assertEquals(parsed_qs['openid.ax.value.ext0.1'][0], user.profile.name)

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_openid_invalid_password(self):

        url = reverse('openid-provider-login')
        user = UserFactory()

        # login to the client so that we can persist session information
        for method in ['POST', 'GET']:
            self.client.login(username=user.username, password='test')
            self.attempt_login(200, method)
            openid_setup = self.client.session['openid_setup']
            self.assertIn('post_params', openid_setup)
            post_args = {
                'email': user.email,
                'password': 'bad_password',
            }

            # call url again, this time with username and password
            resp = self.client.post(url, post_args)
            self.assertEquals(resp.status_code, 302)
            redirect_url = resp['Location']
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url[4])
            self.assertIn('openid.return_to', query_params)
            self.assertTrue(
                query_params['openid.return_to'][0].startswith('http://testserver/openid/complete/')
            )


class OpenIdProviderLiveServerTest(LiveServerTestCase):
    """
    In order for this absolute URL to work (i.e. to get xrds, then authentication)
    in the test environment, we either need a live server that works with the default
    fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
    Here we do the former.
    """

    @skipUnless(settings.FEATURES.get('AUTH_USE_OPENID') and
                settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'),
                'OpenID not enabled')
    def test_begin_login(self):
        # the provider URL must be converted to an absolute URL in order to be
        # used as an openid provider.
        provider_url = reverse('openid-provider-xrds')
        factory = RequestFactory()
        request = factory.request()
        abs_provider_url = request.build_absolute_uri(location=provider_url)

        # In order for this absolute URL to work (i.e. to get xrds, then authentication)
        # in the test environment, we either need a live server that works with the default
        # fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
        # Here we do the latter:
        fetcher = MyFetcher(self.client)
        openid.fetchers.setDefaultFetcher(fetcher, wrap_exceptions=False)

        # now we can begin the login process by invoking a local openid client,
        # with a pointer to the (also-local) openid provider:
        with self.settings(OPENID_SSO_SERVER_URL=abs_provider_url):
            url = reverse('openid-login')
            resp = self.client.post(url)
            code = 200
            self.assertEqual(resp.status_code, code,
                             "got code {0} for url '{1}'. Expected code {2}"
                             .format(resp.status_code, url, code))

    @classmethod
    def tearDownClass(cls):
        """
        Workaround for a runtime error that occurs
        intermittently when the server thread doesn't shut down
        within 2 seconds.

        Since the server is running in a Django thread and will
        be terminated when the test suite terminates,
        this shouldn't cause a resource allocation issue.
        """
        try:
            super(OpenIdProviderLiveServerTest, cls).tearDownClass()
        except RuntimeError:
            print "Warning: Could not shut down test server."
