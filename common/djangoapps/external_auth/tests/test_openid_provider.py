'''
Created on Jan 18, 2013

@author: brian
'''
import openid
from openid.fetchers import HTTPFetcher, HTTPResponse
from urlparse import parse_qs

from django.conf import settings
from django.test import TestCase, LiveServerTestCase
# from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

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

#    def setUp(self):
#        username = 'viewtest'
#        email = 'view@test.com'
#        password = 'foo'
#        user = User.objects.create_user(username, email, password)

    def testBeginLoginWithXrdsUrl(self):
        # skip the test if openid is not enabled (as in cms.envs.test):
        if not settings.MITX_FEATURES.get('AUTH_USE_OPENID') or not settings.MITX_FEATURES.get('AUTH_USE_OPENID_PROVIDER'):
            return

        # the provider URL must be converted to an absolute URL in order to be
        # used as an openid provider.
        provider_url = reverse('openid-provider-xrds')
        factory = RequestFactory()
        request = factory.request()
        abs_provider_url = request.build_absolute_uri(location = provider_url)

        # In order for this absolute URL to work (i.e. to get xrds, then authentication)
        # in the test environment, we either need a live server that works with the default
        # fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
        # Here we do the latter:
        fetcher = MyFetcher(self.client)
        openid.fetchers.setDefaultFetcher(fetcher, wrap_exceptions=False)
        
        # now we can begin the login process by invoking a local openid client,
        # with a pointer to the (also-local) openid provider:
        with self.settings(OPENID_SSO_SERVER_URL = abs_provider_url):
            url = reverse('openid-login')
            resp = self.client.post(url)
            code = 200
            self.assertEqual(resp.status_code, code,
                             "got code {0} for url '{1}'. Expected code {2}"
                             .format(resp.status_code, url, code))

    def testBeginLoginWithLoginUrl(self):
        # skip the test if openid is not enabled (as in cms.envs.test):
        if not settings.MITX_FEATURES.get('AUTH_USE_OPENID') or not settings.MITX_FEATURES.get('AUTH_USE_OPENID_PROVIDER'):
            return

        # the provider URL must be converted to an absolute URL in order to be
        # used as an openid provider.
        provider_url = reverse('openid-provider-login')
        factory = RequestFactory()
        request = factory.request()
        abs_provider_url = request.build_absolute_uri(location = provider_url)

        # In order for this absolute URL to work (i.e. to get xrds, then authentication)
        # in the test environment, we either need a live server that works with the default
        # fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
        # Here we do the latter:
        fetcher = MyFetcher(self.client)
        openid.fetchers.setDefaultFetcher(fetcher, wrap_exceptions=False)
        
        # now we can begin the login process by invoking a local openid client,
        # with a pointer to the (also-local) openid provider:
        with self.settings(OPENID_SSO_SERVER_URL = abs_provider_url):
            url = reverse('openid-login')
            resp = self.client.post(url)
            code = 200
            self.assertEqual(resp.status_code, code,
                             "got code {0} for url '{1}'. Expected code {2}"
                             .format(resp.status_code, url, code))
            
# In order for this absolute URL to work (i.e. to get xrds, then authentication)
# in the test environment, we either need a live server that works with the default
# fetcher (i.e. urlopen2), or a test server that is reached through a custom fetcher.
# Here we do the former.
class OpenIdProviderLiveServerTest(LiveServerTestCase):

    def testBeginLogin(self):
        # skip the test if openid is not enabled (as in cms.envs.test):
        if not settings.MITX_FEATURES.get('AUTH_USE_OPENID') or not settings.MITX_FEATURES.get('AUTH_USE_OPENID_PROVIDER'):
            return

        # the provider URL must be converted to an absolute URL in order to be
        # used as an openid provider.
        provider_url = reverse('openid-provider-xrds')
        factory = RequestFactory()
        request = factory.request()
        abs_provider_url = request.build_absolute_uri(location = provider_url)

        # now we can begin the login process by invoking a local openid client,
        # with a pointer to the (also-local) openid provider:
        with self.settings(OPENID_SSO_SERVER_URL = abs_provider_url):
            url = reverse('openid-login')
            resp = self.client.post(url)
            code = 200
            self.assertEqual(resp.status_code, code,
                             "got code {0} for url '{1}'. Expected code {2}"
                             .format(resp.status_code, url, code))
