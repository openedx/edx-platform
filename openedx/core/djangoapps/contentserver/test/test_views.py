"""
Tests for the view version of course asset serving.
"""

import ddt
from django.test import TestCase
from django.urls import resolve


@ddt.ddt
class UrlsTest(TestCase):
    """
    Tests for ensuring that the urlpatterns registered to the view are
    appropriate for the URLs that the middleware historically handled.
    """

    @ddt.data(
        '/c4x/edX/Open_DemoX/asset/images_course_image.jpg',
        '/asset-v1:edX+DemoX.1+2T2019+type@asset+block/DemoX-poster.jpg',
        '/assets/courseware/v1/0123456789abcdef0123456789abcdef/asset-v1:edX+FAKE101+2024+type@asset+block/HW1.png',
    )
    def test_sample_urls(self, sample_url):
        """
        Regression test -- c4x URL was previously incorrect in urls.py.
        """
        assert resolve(sample_url).view_name == 'openedx.core.djangoapps.contentserver.views.course_assets_view'
