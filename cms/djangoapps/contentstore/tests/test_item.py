from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from django.core.urlresolvers import reverse


class DeleteItem(CourseTestCase):
    def setUp(self):
        """ Creates the test course with a static page in it. """
        super(DeleteItem, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Dummy Course')

    def testDeleteStaticPage(self):
        # Add static tab
        data = {
            'parent_location': 'i4x://mitX/333/course/Dummy_Course',
            'template': 'i4x://edx/templates/static_tab/Empty'
        }

        resp = self.client.post(reverse('clone_item'), data)
        self.assertEqual(resp.status_code, 200)

        # Now delete it. There was a bug that the delete was failing (static tabs do not exist in draft modulestore).
        resp = self.client.post(reverse('delete_item'), resp.content, "application/json")
        self.assertEqual(resp.status_code, 200)




