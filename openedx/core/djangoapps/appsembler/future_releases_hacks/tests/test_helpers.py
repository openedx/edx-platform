"""
Tests for upgrade hack helpers
"""

import unittest

import ddt
from openedx.core.djangoapps.appsembler.future_releases_hacks.helpers import replace_jump_with_resume


@ddt.ddt
class TestReplaceJumpWithResume(unittest.TestCase):
    """
    Test replace_jump_with_resume helper
    """
    @ddt.data(
        (
            '/courses/a-course-id:whatever/jump_to/some/link@whatever',
            '/courses/a-course-id:whatever/resume_to/some/link@whatever'
        ),
        (
            '/courses/a-course-id:the-course-id-is-jump_to/jump_to/some/link@whatever',
            '/courses/a-course-id:the-course-id-is-jump_to/resume_to/some/link@whatever'
        ),
        (
            'https://a-domain.something/courses/a-course-id:whatever/jump_to/some/link@whatever',
            'https://a-domain.something/courses/a-course-id:whatever/resume_to/some/link@whatever'
        ),
    )
    @ddt.unpack
    def test_valid_url(self, jump_link, expected_link):
        """
        Verify that the helper returns the expected value
        """
        self.assertEqual(expected_link, replace_jump_with_resume(jump_link))

    @ddt.data(
        '/notcourses/a-course-id:whatever/jump_to/some/link@whatever',
        '/courses/a-course-id:whatever/nojump_to/some/link@whatever',
        '/courses/a-course-id:whatever/jump_to',  # nothing after jump_to
        '/courses/a-course-id:whatever/jump_to/',  # nothing after jump_to
        '/courses/jump_to/some/link@whatever',  # no course
    )
    def test_invalid_links(self, jump_link):
        """
        Verify that replace_jump_with_resume will return the link as it is if it cannot recognize it
        """
        self.assertEqual(jump_link, replace_jump_with_resume(jump_link))
