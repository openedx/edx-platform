# pylint: disable=missing-docstring,maybe-no-member

from unittest import TestCase

from track import contexts


class TestContexts(TestCase):

    ORG_ID = 'test'
    COURSE = 'course_name'
    RUN = 'course_run'
    COURSE_ID = '/'.join((ORG_ID, COURSE, RUN))
    COURSE_KEY = 'course-v1:' + '+'.join((ORG_ID, COURSE, RUN))

    def test_course_id_from_url(self):
        self.assert_parses_course_id_from_url('http://foo.bar.com/courses/{course_id}/more/stuff')

    def assert_parses_course_id_from_url(self, format_string, course_id=COURSE_ID):
        self.assertEquals(
            contexts.course_context_from_url(format_string.format(course_id=course_id)),
            {
                'course_id': course_id,
                'org_id': self.ORG_ID,
                'course_key': {
                    'org': self.ORG_ID,
                    'course': self.COURSE,
                    'run': self.RUN
                },
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

    def test_course_v1(self):
        self.assert_parses_course_id_from_url('http://foo.bar.com/courses/{course_id}/other/stuff', course_id=self.COURSE_KEY)

    def test_course_v1_later_in_url(self):
        self.assert_parses_course_id_from_url('http://foo.bar.com/x/y/z/courses/{course_id}/other/stuff', course_id=self.COURSE_KEY)
