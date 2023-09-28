"""
Tests for the legacy course home page.
"""

from django.test import TestCase


class TestCourseHomePage(TestCase):
    """Tests for the legacy course home page (the legacy course outline tab)"""
    def test_legacy_redirect(self):
        """
        Verify that the legacy course home page redirects to the MFE correctly.
        """
        response = self.client.get('/courses/course-v1:edX+test+Test_Course/course/?foo=b$r')
        assert response.status_code == 302
        assert response.get('Location') == 'http://learning-mfe/course/course-v1:edX+test+Test_Course/home?foo=b%24r'
