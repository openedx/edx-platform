"""
Tests for the rss_proxy views
"""


from django.test import TestCase
from django.urls import reverse
from mock import Mock, patch

from lms.djangoapps.rss_proxy.models import WhitelistedRssUrl


class RssProxyViewTests(TestCase):
    """ Tests for the rss_proxy views """

    def setUp(self):
        super(RssProxyViewTests, self).setUp()

        self.whitelisted_url1 = 'http://www.example.com'
        self.whitelisted_url2 = 'http://www.example.org'
        self.non_whitelisted_url = 'http://www.example.net'
        self.rss = '''
            <?xml version="1.0" encoding="utf-8" ?>
            <rss version="2.0">
                <channel>
                    <title></title>
                    <link>http://www.example.com/rss</link>
                    <description></description>
                    <language>en</language>
                    <item>
                        <title>Example</title>
                        <link>http://www.example.com/rss/item</link>
                        <description>Example item description</description>
                        <pubDate>Fri, 13 May 1977 00:00:00 +0000</pubDate>
                    </item>
                </channel>
            </rss>
        '''
        WhitelistedRssUrl.objects.create(url=self.whitelisted_url1)
        WhitelistedRssUrl.objects.create(url=self.whitelisted_url2)

    @patch('lms.djangoapps.rss_proxy.views.requests.get')
    def test_proxy_with_whitelisted_url(self, mock_requests_get):
        """
        Test the proxy view with a whitelisted URL
        """
        mock_requests_get.return_value = Mock(status_code=200, content=self.rss)
        resp = self.client.get('%s?url=%s' % (reverse('rss_proxy:proxy'), self.whitelisted_url1))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/xml')
        self.assertEqual(resp.content.decode('utf-8'), self.rss)

    @patch('lms.djangoapps.rss_proxy.views.requests.get')
    def test_proxy_with_whitelisted_url_404(self, mock_requests_get):
        """
        Test the proxy view with a whitelisted URL that is not found
        """
        mock_requests_get.return_value = Mock(status_code=404)
        resp = self.client.get('%s?url=%s' % (reverse('rss_proxy:proxy'), self.whitelisted_url2))
        print(resp.status_code)
        print(resp.content)
        print(resp['Content-Type'])
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp['Content-Type'], 'application/xml')
        self.assertEqual(resp.content.decode('utf-8'), '')

    def test_proxy_with_non_whitelisted_url(self):
        """
        Test the proxy view with a non-whitelisted URL
        """
        resp = self.client.get('%s?url=%s' % (reverse('rss_proxy:proxy'), self.non_whitelisted_url))
        self.assertEqual(resp.status_code, 404)
