# pylint: disable=missing-docstring,maybe-no-member

from unittest import TestCase

from track import contexts


class TestContexts(TestCase):

    COURSE_ID = 'test/course_name/course_run'
    ORG_ID = 'test'

    def test_course_id_from_url(self):
        self.assert_parses_course_id_from_url('http://foo.bar.com/courses/{course_id}/more/stuff')

    def assert_parses_course_id_from_url(self, format_string):
        self.assertEquals(
            contexts.course_context_from_url(format_string.format(course_id=self.COURSE_ID)),
            {
                'course_id': self.COURSE_ID,
                'org_id': self.ORG_ID
            }
        )

    def test_no_course_id_in_url(self):
        self.assert_empty_context_for_url('http://foo.bar.com/dashboard')

    def assert_empty_context_for_url(self, url):
        self.assertEquals(
            contexts.course_context_from_url(url),
            {
                'course_id': '',
                'org_id': ''
            }
        )

    def test_malformed_course_id(self):
        self.assert_empty_context_for_url('http://foo.bar.com/courses/test')

    def test_course_id_later_in_url(self):
        self.assert_parses_course_id_from_url('http://foo.bar.com/x/y/z/courses/{course_id}')

    def test_no_url(self):
        self.assert_empty_context_for_url(None)
