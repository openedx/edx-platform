"""
integration tests for xmodule

Contains:

    1. BaseTestXmodule class provides course and users
    for testing Xmodules with mongo store.
"""

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.test.client import Client

from edxmako.shortcuts import render_to_string
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_MONGO_MODULESTORE
from xblock.field_data import DictFieldData
from xmodule.tests import get_test_system, get_test_descriptor_system
from opaque_keys.edx.locations import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from lms.djangoapps.lms_xblock.runtime import quote_slashes


class BaseTestXmodule(ModuleStoreTestCase):
    """Base class for testing Xmodules with mongo store.

    This class prepares course and users for tests:
        1. create test course;
        2. create, enroll and login users for this course;

    Any xmodule should overwrite only next parameters for test:
        1. CATEGORY
        2. DATA or METADATA
        3. MODEL_DATA
        4. COURSE_DATA and USER_COUNT if needed

    This class should not contain any tests, because CATEGORY
    should be defined in child class.
    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE

    USER_COUNT = 2
    COURSE_DATA = {}

    # Data from YAML common/lib/xmodule/xmodule/templates/NAME/default.yaml
    CATEGORY = "vertical"
    DATA = ''
    # METADATA must be overwritten for every instance that uses it. Otherwise,
    # if we'll change it in the tests, it will be changed for all other instances
    # of parent class.
    METADATA = {}
    MODEL_DATA = {'data': '<some_module></some_module>'}

    def new_module_runtime(self):
        """
        Generate a new ModuleSystem that is minimally set up for testing
        """
        return get_test_system(course_id=self.course.id)

    def new_descriptor_runtime(self):
        runtime = get_test_descriptor_system()
        runtime.get_block = modulestore().get_item
        return runtime

    def initialize_module(self, **kwargs):
        kwargs.update({
            'parent_location': self.section.location,
            'category': self.CATEGORY
        })

        self.item_descriptor = ItemFactory.create(**kwargs)

        self.runtime = self.new_descriptor_runtime()

        field_data = {}
        field_data.update(self.MODEL_DATA)
        student_data = DictFieldData(field_data)
        self.item_descriptor._field_data = LmsFieldData(self.item_descriptor._field_data, student_data)

        self.item_descriptor.xmodule_runtime = self.new_module_runtime()

        self.item_url = unicode(self.item_descriptor.location)

    def setup_course(self):
        self.course = CourseFactory.create(data=self.COURSE_DATA)

        # Turn off cache.
        modulestore().request_cache = None
        modulestore().metadata_inheritance_cache_subsystem = None

        chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="sequential",
        )
        self.section = ItemFactory.create(
            parent_location=chapter.location,
            category="sequential"
        )

        # username = robot{0}, password = 'test'
        self.users = [
            UserFactory.create()
            for dummy0 in range(self.USER_COUNT)
        ]

        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        # login all users for acces to Xmodule
        self.clients = {user.username: Client() for user in self.users}
        self.login_statuses = [
            self.clients[user.username].login(
                username=user.username, password='test')
            for user in self.users
        ]

        self.assertTrue(all(self.login_statuses))

    def setUp(self):
        super(BaseTestXmodule, self).setUp()
        self.setup_course()
        self.initialize_module(metadata=self.METADATA, data=self.DATA)

    def get_url(self, dispatch):
        """Return item url with dispatch."""
        return reverse(
            'xblock_handler',
            args=(unicode(self.course.id), quote_slashes(self.item_url), 'xmodule_handler', dispatch)
        )


class XModuleRenderingTestBase(BaseTestXmodule):

    def new_module_runtime(self):
        """
        Create a runtime that actually does html rendering
        """
        runtime = super(XModuleRenderingTestBase, self).new_module_runtime()
        runtime.render_template = render_to_string
        return runtime
