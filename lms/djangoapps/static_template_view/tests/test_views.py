"""
Tests for static templates
"""
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse


class MarketingSiteViewTests(TestCase):
    """ Tests for the marketing site views """

    def _test_view(self, view_name, mimetype):
        resp = self.client.get(reverse(view_name))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], mimetype)

    def test_sitemap(self):
        """
        Test the sitemap view
        """
        self._test_view('sitemap_xml', 'application/xml')

    def test_about(self):
        """
        Test the about view
        """
        self._test_view('about', 'text/html')

    def test_404(self):
        """
        Test the 404 view.
        """
        url = reverse('static_template_view.views.render_404')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/html')
        resp = self.client.get(url)
        self.assertContains(resp, settings.TECH_SUPPORT_EMAIL)

    def test_500(self):
        """
        Test the 500 view.
        """
        url = reverse('static_template_view.views.render_500')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')

        # check response with branding
        resp = self.client.get(url)
        self.assertContains(
            resp,
            'There has been a 500 error on the <em>{platform_name}</em> servers'.format(
                platform_name=settings.PLATFORM_NAME
            ),
            status_code=500
        )
        self.assertContains(resp, settings.TECH_SUPPORT_EMAIL, status_code=500)

    def test_404_microsites(self):
        """
        Test the 404 view as if called in a microsite.
        """
        url = reverse('static_template_view.views.render_404')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/html')

        # check response with branding
        resp = self.client.get(url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertContains(resp, settings.MICROSITE_CONFIGURATION['test_site']['email_from_address'])

    def test_500_microsites(self):
        """
        Test the 500 view as if called in a microsite.
        """
        url = reverse('static_template_view.views.render_500')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')

        # check response with branding
        resp = self.client.get(url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertContains(
            resp,
            'There has been a 500 error on the <em>{platform_name}</em> servers'.format(
                platform_name=settings.MICROSITE_CONFIGURATION['test_site']['platform_name']
            ),
            status_code=500
        )
        self.assertContains(
            resp,
            settings.MICROSITE_CONFIGURATION['test_site']['email_from_address'],
            status_code=500
        )
