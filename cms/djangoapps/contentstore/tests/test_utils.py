""" Tests for utils. """
from contentstore import utils
import mock
from django.test import TestCase
from xmodule.modulestore.tests.factories import CourseFactory
from .utils import ModuleStoreTestCase


class LMSLinksTestCase(TestCase):
    """ Tests for LMS links. """
    def about_page_test(self):
        """ Get URL for about page. """
        location = 'i4x', 'mitX', '101', 'course', 'test'
        utils.get_course_id = mock.Mock(return_value="mitX/101/test")
        link = utils.get_lms_link_for_about_page(location)
        self.assertEquals(link, "//localhost:8000/courses/mitX/101/test/about")

    def lms_link_test(self):
        """ Tests get_lms_link_for_item. """
        location = 'i4x', 'mitX', '101', 'vertical', 'contacting_us'
        utils.get_course_id = mock.Mock(return_value="mitX/101/test")
        link = utils.get_lms_link_for_item(location, False)
        self.assertEquals(link, "//localhost:8000/courses/mitX/101/test/jump_to/i4x://mitX/101/vertical/contacting_us")
        link = utils.get_lms_link_for_item(location, True)
        self.assertEquals(
            link,
            "//preview.localhost:8000/courses/mitX/101/test/jump_to/i4x://mitX/101/vertical/contacting_us"
        )


class UrlReverseTestCase(ModuleStoreTestCase):
    """ Tests for get_url_reverse """
    def test_CoursePageNames(self):
        """ Test the defined course pages. """
        course = CourseFactory.create(org='mitX', number='666', display_name='URL Reverse Course')

        self.assertEquals(
            '/manage_users/i4x://mitX/666/course/URL_Reverse_Course',
            utils.get_url_reverse('ManageUsers', course)
        )

        self.assertEquals(
            '/mitX/666/settings-details/URL_Reverse_Course',
            utils.get_url_reverse('SettingsDetails', course)
        )

        self.assertEquals(
            '/mitX/666/settings-grading/URL_Reverse_Course',
            utils.get_url_reverse('SettingsGrading', course)
        )

        self.assertEquals(
            '/mitX/666/course/URL_Reverse_Course',
            utils.get_url_reverse('CourseOutline', course)
        )

        self.assertEquals(
            '/mitX/666/checklists/URL_Reverse_Course',
            utils.get_url_reverse('Checklists', course)
        )

    def test_unknown_passes_through(self):
        """ Test that unknown values pass through. """
        course = CourseFactory.create(org='mitX', number='666', display_name='URL Reverse Course')
        self.assertEquals(
            'foobar',
            utils.get_url_reverse('foobar', course)
        )
        self.assertEquals(
            'https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/about',
            utils.get_url_reverse('https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/about', course)
        )