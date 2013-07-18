from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from django.core.urlresolvers import reverse
from xmodule.capa_module import CapaDescriptor
import json
from xmodule.modulestore.django import modulestore


class DeleteItem(CourseTestCase):
    def setUp(self):
        """ Creates the test course with a static page in it. """
        super(DeleteItem, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Dummy Course')

    def testDeleteStaticPage(self):
        # Add static tab
        data = json.dumps({
            'parent_location': 'i4x://mitX/333/course/Dummy_Course',
            'category': 'static_tab'
        })

        resp = self.client.post(reverse('create_item'), data,
            content_type="application/json")
        self.assertEqual(resp.status_code, 200)

        # Now delete it. There was a bug that the delete was failing (static tabs do not exist in draft modulestore).
        resp = self.client.post(reverse('delete_item'), resp.content, "application/json")
        self.assertEqual(resp.status_code, 200)


class TestCreateItem(CourseTestCase):
    """
    Test the create_item handler thoroughly
    """
    def response_id(self, response):
        """
        Get the id from the response payload
        :param response:
        """
        parsed = json.loads(response.content)
        return parsed['id']

    def test_create_nicely(self):
        """
        Try the straightforward use cases
        """
        # create a chapter
        display_name = 'Nicely created'
        resp = self.client.post(
            reverse('create_item'),
            json.dumps({
                'parent_location': self.course.location.url(),
                'display_name': display_name,
                'category': 'chapter'
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)

        # get the new item and check its category and display_name
        chap_location = self.response_id(resp)
        new_obj = modulestore().get_item(chap_location)
        self.assertEqual(new_obj.category, 'chapter')
        self.assertEqual(new_obj.display_name, display_name)
        self.assertEqual(new_obj.location.org, self.course.location.org)
        self.assertEqual(new_obj.location.course, self.course.location.course)

        # get the course and ensure it now points to this one
        course = modulestore().get_item(self.course.location)
        self.assertIn(chap_location, course.children)

        # use default display name
        resp = self.client.post(
            reverse('create_item'),
            json.dumps({
                'parent_location': chap_location,
                'category': 'vertical'
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)

        vert_location = self.response_id(resp)

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.client.post(
            reverse('create_item'),
            json.dumps({
                'parent_location': vert_location,
                'category': 'problem',
                'boilerplate': template_id
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        prob_location = self.response_id(resp)
        problem = modulestore('draft').get_item(prob_location)
        # ensure it's draft
        self.assertTrue(problem.is_draft)
        # check against the template
        template = CapaDescriptor.get_template(template_id)
        self.assertEqual(problem.data, template['data'])
        self.assertEqual(problem.display_name, template['metadata']['display_name'])
        self.assertEqual(problem.markdown, template['metadata']['markdown'])

    def test_create_item_negative(self):
        """
        Negative tests for create_item
        """
        # non-existent boilerplate: creates a default
        resp = self.client.post(
            reverse('create_item'),
            json.dumps(
                {'parent_location': self.course.location.url(),
                 'category': 'problem',
                 'boilerplate': 'nosuchboilerplate.yaml'
                 }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)

class TestEditItem(CourseTestCase):
    """
    Test contentstore.views.item.save_item
    """
    def response_id(self, response):
        """
        Get the id from the response payload
        :param response:
        """
        parsed = json.loads(response.content)
        return parsed['id']

    def setUp(self):
        """ Creates the test course structure and a couple problems to 'edit'. """
        super(TestEditItem, self).setUp()
        # create a chapter
        display_name = 'chapter created'
        resp = self.client.post(
            reverse('create_item'),
            json.dumps(
                {'parent_location': self.course.location.url(),
                 'display_name': display_name,
                 'category': 'chapter'
                 }),
            content_type="application/json"
        )
        chap_location = self.response_id(resp)
        resp = self.client.post(
            reverse('create_item'),
            json.dumps(
                {'parent_location': chap_location,
                 'category': 'vertical'
                }),
            content_type="application/json"
        )
        vert_location = self.response_id(resp)
        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.client.post(
            reverse('create_item'),
            json.dumps({'parent_location': vert_location,
             'category': 'problem',
             'boilerplate': template_id
            }),
            content_type="application/json"
        )
        self.problems = [self.response_id(resp)]

    def test_delete_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        self.client.post(
            reverse('save_item'),
            json.dumps({
                'id': self.problems[0],
                'metadata': {'rerandomize': 'onreset'}
            }),
            content_type="application/json"
        )
        problem = modulestore('draft').get_item(self.problems[0])
        self.assertEqual(problem.rerandomize, 'onreset')
        self.client.post(
            reverse('save_item'),
            json.dumps({
                'id': self.problems[0],
                'metadata': {'rerandomize': None}
            }),
            content_type="application/json"
        )
        problem = modulestore('draft').get_item(self.problems[0])
        self.assertEqual(problem.rerandomize, 'never')


    def test_null_field(self):
        """
        Sending null in for a field 'deletes' it
        """
        problem = modulestore('draft').get_item(self.problems[0])
        self.assertIsNotNone(problem.markdown)
        self.client.post(
            reverse('save_item'),
            json.dumps({
                'id': self.problems[0],
                'nullout': ['markdown']
            }),
            content_type="application/json"
        )
        problem = modulestore('draft').get_item(self.problems[0])
        self.assertIsNone(problem.markdown)
