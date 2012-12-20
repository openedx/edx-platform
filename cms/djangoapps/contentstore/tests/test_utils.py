from django.test.testcases import TestCase
from  cms.djangoapps.contentstore import utils
import mock

class LMSLinksTestCase(TestCase):
    def about_page_test(self):
        location = 'i4x','mitX','101','course', 'test'
        utils.get_course_id = mock.Mock(return_value="mitX/101/test")
        link = utils.get_lms_link_for_about_page(location)
        self.assertEquals(link, "//localhost:8000/courses/mitX/101/test/about")

    def ls_link_test(self):
        location = 'i4x','mitX','101','vertical', 'contacting_us'
        utils.get_course_id = mock.Mock(return_value="mitX/101/test")
        link = utils.get_lms_link_for_item(location, False)
        self.assertEquals(link, "//localhost:8000/courses/mitX/101/test/jump_to/i4x://mitX/101/vertical/contacting_us")
        link = utils.get_lms_link_for_item(location, True)
        self.assertEquals(link, "//preview.localhost:8000/courses/mitX/101/test/jump_to/i4x://mitX/101/vertical/contacting_us")
