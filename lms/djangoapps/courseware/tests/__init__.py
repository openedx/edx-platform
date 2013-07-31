"""
integration tests for xmodule

Contains:

    1. BaseTestXmodule class provides course and users
    for testing Xmodules with mongo store.
"""

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.test.client import Client

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.tests import get_test_system
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class BaseTestXmodule(ModuleStoreTestCase):
    """Base class for testing Xmodules with mongo store.

    This class prepares course and users for tests:
        1. create test course;
        2. create, enroll and login users for this course;

    Any xmodule should overwrite only next parameters for test:
        1. CATEGORY
        2. DATA
        3. MODEL_DATA
        4. COURSE_DATA and USER_COUNT if needed

    This class should not contain any tests, because CATEGORY
    should be defined in child class.
    """
    USER_COUNT = 2
    COURSE_DATA = {}

    # Data from YAML common/lib/xmodule/xmodule/templates/NAME/default.yaml
    CATEGORY = ""
    DATA = ''
    MODEL_DATA = {'data': '<some_module></some_module>'}

    def setUp(self):

        self.course = CourseFactory.create(data=self.COURSE_DATA)

        # Turn off cache.
        modulestore().request_cache = None
        modulestore().metadata_inheritance_cache_subsystem = None

        chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="sequential",
        )
        section = ItemFactory.create(
            parent_location=chapter.location,
            category="sequential"
        )

        # username = robot{0}, password = 'test'
        self.users = [
            UserFactory.create(username='robot%d' % i, email='robot+test+%d@edx.org' % i)
            for i in range(self.USER_COUNT)
        ]

        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        self.item_descriptor = ItemFactory.create(
            parent_location=section.location,
            category=self.CATEGORY,
            data=self.DATA
        )

        self.runtime = get_test_system()
        # Allow us to assert that the template was called in the same way from
        # different code paths while maintaining the type returned by render_template
        self.runtime.render_template = lambda template, context: unicode((template, sorted(context.items())))
        model_data = {'location': self.item_descriptor.location}
        model_data.update(self.MODEL_DATA)

        self.item_module = self.item_descriptor.module_class(
            self.runtime, self.item_descriptor, model_data
        )
        self.item_url = Location(self.item_module.location).url()

        # login all users for acces to Xmodule
        self.clients = {user.username: Client() for user in self.users}
        self.login_statuses = [
            self.clients[user.username].login(
                username=user.username, password='test')
            for user in self.users
        ]

        self.assertTrue(all(self.login_statuses))

    def get_url(self, dispatch):
        """Return item url with dispatch."""
        return reverse(
            'modx_dispatch',
            args=(self.course.id, self.item_url, dispatch)
        )

    def tearDown(self):
        for user in self.users:
            user.delete()
