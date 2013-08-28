import json

from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from mock import patch, MagicMock

from courseware.models import XModuleContentField
import courseware.module_render as module_render
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.model_data import ModelDataCache
import instructor.hint_manager as view
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class HintManagerTest(ModuleStoreTestCase):

    def setUp(self):
        """
        Makes a course, which will be the same for all tests.
        Set up mako middleware, which is necessary for template rendering to happen.
        """
        from mitxmako.middleware import MakoMiddleware
        MakoMiddleware()
        self.course = CourseFactory.create(org='Me', number='19.002', display_name='test_course')
        self.url = '/courses/Me/19.002/test_course/hint_manager'
        self.user = UserFactory.create(username='robot', email='robot@edx.org', password='test', is_staff=True)
        self.c = Client()
        self.c.login(username='robot', password='test')
        self.model_data_cache = ModelDataCache(
            [self.course],
            self.course.id,
            self.user,
        )
        self.problem_descriptor = ItemFactory(
            parent_location=self.course.location,
            category='problem',
            data='''
            <problem>
                <numericalresponse answer="42">
                    <responseparam type="tolerance" default="0.00001"/>
                    <textline size="20" inline="true" trailing_text="kN"/>
                </numericalresponse>
            </problem>
            '''
        )
        self.problem_id = str(self.problem_descriptor.location)
        self.hinter_descriptor = ItemFactory(
            parent_location=self.course.location,
            category='crowdsource_hinter',
            data='<crowdsource_hinter />'
        )
        self.hinter_id = str(self.hinter_descriptor.location)
        # Instantiate this descriptor into an xmodule, and set a bunch of properties.
        hinter_xmodule = self._fetch_xmodule(self.hinter_descriptor)
        hinter_xmodule.target_problem = str(self.problem_descriptor.location)
        hinter_xmodule.hints = {
            '1.0': {
                '1': ['Hint 1', 2],
                '3': ['Hint 3', 12]
            },
            '2.0': {
                '4': ['Hint 4', 3]
            }
        }
        hinter_xmodule.mod_queue = {'2.0': {'2': ['Hint 2', 1]}}
        hinter_xmodule.hint_pk = 5
        hinter_xmodule.save()

    def _fetch_xmodule(self, descriptor):
        """
        Given a descriptor, return an xmodule.
        """
        return module_render.get_module_for_descriptor_internal(
            self.user,
            descriptor,
            self.model_data_cache,
            self.course.id,
            lambda *args: None,
            'blah',
        )

    def test_student_block(self):
        """
        Makes sure that students cannot see the hint management view.
        """
        c = Client()
        UserFactory.create(username='student', email='student@edx.org', password='test')
        c.login(username='student', password='test')
        out = c.get(self.url)
        print out
        self.assertTrue('Sorry, but students are not allowed to access the hint manager!' in out.content)

    def test_staff_access(self):
        """
        Makes sure that staff can access the hint management view.
        """
        out = self.c.get('/courses/Me/19.002/test_course/hint_manager')
        print out
        self.assertTrue('Hints Awaiting Moderation' in out.content)

    def test_invalid_field_access(self):
        """
        Makes sure that field names other than 'mod_queue' and 'hints' are
        rejected.
        """
        out = self.c.post(self.url, {'op': 'delete hints', 'field': 'all your private data'})
        print out
        self.assertTrue('an invalid field was accessed' in out.content)

    def test_switchfields(self):
        """
        Checks that the op: 'switch fields' POST request works.
        """
        out = self.c.post(self.url, {'op': 'switch fields', 'field': 'mod_queue'})
        print out
        self.assertTrue('Hint 2' in out.content)

    def test_gethints(self):
        """
        Checks that gethints returns the right data.
        """
        request = RequestFactory()
        post = request.post(self.url, {'field': 'mod_queue'})
        post.user = self.user
        post.session = MagicMock()
        out = view.get_hints(post, self.course.id, 'mod_queue')
        print out
        self.assertTrue(out['other_field'] == 'hints')
        expected = {self.problem_id: [(u'2.0', {u'2': [u'Hint 2', 1]})]}
        self.assertTrue(out['all_hints'] == expected)

    def test_gethints_other(self):
        """
        Same as above, with hints instead of mod_queue
        """
        request = RequestFactory()
        post = request.post(self.url, {'field': 'hints'})
        post.user = self.user
        post.session = MagicMock()
        out = view.get_hints(post, self.course.id, 'hints')
        print out
        self.assertTrue(out['other_field'] == 'mod_queue')
        expected = {self.problem_id: [('1.0', {'1': ['Hint 1', 2],
                                               '3': ['Hint 3', 12]}),
                                      ('2.0', {'4': ['Hint 4', 3]})
                                      ]}
        self.assertTrue(out['all_hints'] == expected)

    def test_deletehints(self):
        """
        Checks that delete_hints deletes the right stuff.
        """
        request = RequestFactory()
        post = request.post(self.url, {'field': 'hints',
                                       'op': 'delete hints',
                                       1: [self.hinter_id, '1.0', '1']})
        post.user = self.user
        post.session = MagicMock()
        view.delete_hints(post, self.course.id, 'hints')
        problem_hints = XModuleContentField.objects.get(field_name='hints', definition_id=self.problem_id).value
        self.assertTrue('1' not in json.loads(problem_hints)['1.0'])

    def test_changevotes(self):
        """
        Checks that vote changing works.
        """
        request = RequestFactory()
        post = request.post(self.url, {'field': 'hints',
                                       'op': 'change votes',
                                       1: [self.hinter_id, '1.0', '1', 5]})
        post.user = self.user
        post.session = MagicMock()
        view.change_votes(post, self.course.id, 'hints')
        problem_hints = XModuleContentField.objects.get(field_name='hints', definition_id=self.problem_id).value
        # hints[answer][hint_pk (string)] = [hint text, vote count]
        print json.loads(problem_hints)['1.0']['1']
        self.assertTrue(json.loads(problem_hints)['1.0']['1'][1] == 5)

    def test_addhint(self):
        """
        Check that instructors can add new hints.
        """
        # Because add_hint accesses the xmodule, this test requires a bunch
        # of monkey patching.
        hinter = MagicMock()
        hinter.validate_answer = lambda string: True

        request = RequestFactory()
        post = request.post(self.url, {'field': 'mod_queue',
                                       'op': 'add hint',
                                       'problem': self.hinter_id,
                                       'answer': '3.14',
                                       'hint': 'This is a new hint.'})
        post.user = self.user
        post.session = MagicMock()
        view.add_hint(post, self.course.id, 'mod_queue')
        problem_hints = XModuleContentField.objects.get(field_name='mod_queue', definition_id=self.problem_id).value
        self.assertTrue('3.14' in json.loads(problem_hints))

    def test_addbadhint(self):
        """
        Check that instructors cannot add hints with unparsable answers.
        """
        # Patching.
        hinter = MagicMock()
        hinter.validate_answer = lambda string: False

        request = RequestFactory()
        post = request.post(self.url, {'field': 'mod_queue',
                                       'op': 'add hint',
                                       'problem': self.hinter_id,
                                       'answer': 'fish',
                                       'hint': 'This is a new hint.'})
        post.user = self.user
        post.session = MagicMock()
        view.add_hint(post, self.course.id, 'mod_queue')
        problem_hints = XModuleContentField.objects.get(field_name='mod_queue', definition_id=self.problem_id).value
        self.assertTrue('fish' not in json.loads(problem_hints))

    def test_approve(self):
        """
        Check that instructors can approve hints.  (Move them
        from the mod_queue to the hints.)
        """
        request = RequestFactory()
        post = request.post(self.url, {'field': 'mod_queue',
                                       'op': 'approve',
                                       1: [self.hinter_id, '2.0', '2']})
        post.user = self.user
        post.session = MagicMock()
        view.approve(post, self.course.id, 'mod_queue')
        problem_hints = XModuleContentField.objects.get(field_name='mod_queue', definition_id=self.problem_id).value
        self.assertTrue('2.0' not in json.loads(problem_hints) or len(json.loads(problem_hints)['2.0']) == 0)
        problem_hints = XModuleContentField.objects.get(field_name='hints', definition_id=self.problem_id).value
        self.assertTrue(json.loads(problem_hints)['2.0']['2'] == ['Hint 2', 1])
        self.assertTrue(len(json.loads(problem_hints)['2.0']) == 2)
