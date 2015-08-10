"""
Common test utilities for courseware functionality
"""

from abc import ABCMeta, abstractmethod
from datetime import datetime
import ddt
from mock import patch
from urllib import urlencode

from lms.djangoapps.courseware.field_overrides import OverrideModulestoreFieldData
from lms.djangoapps.courseware.url_helpers import get_redirect_url
from student.tests.factories import AdminFactory, UserFactory, CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls


@ddt.ddt
class RenderXBlockTestMixin(object):
    """
    Mixin for testing the courseware.render_xblock function.
    It can be used for testing any higher-level endpoint that calls this method.
    """
    __metaclass__ = ABCMeta

    # DOM elements that appear in the LMS Courseware,
    # but are excluded from the xBlock-only rendering.
    COURSEWARE_CHROME_HTML_ELEMENTS = [
        '<ol class="tabs course-tabs"',
        '<footer id="footer-openedx"',
        '<div class="window-wrap"',
        '<div class="preview-menu"',
        '<div class="container"'
    ]

    # DOM elements that appear in an xBlock,
    # but are excluded from the xBlock-only rendering.
    XBLOCK_REMOVED_HTML_ELEMENTS = [
        '<div class="wrap-instructor-info"',
    ]

    @abstractmethod
    def get_response(self, url_encoded_params=None):
        """
        Abstract method to get the response from the endpoint that is being tested.

        Arguments:
            url_encoded_params - URL encoded parameters that should be appended to the requested URL.
        """
        pass   # pragma: no cover

    def login(self):
        """
        Logs in the test user.
        """
        self.client.login(username=self.user.username, password='test')

    def course_options(self):
        """
        Options to configure the test course. Intended to be overridden by
        subclasses.
        """
        return {}

    def setup_course(self, default_store=None):
        """
        Helper method to create the course.
        """
        if not default_store:
            default_store = self.store.default_modulestore.get_modulestore_type()
        with self.store.default_store(default_store):
            self.course = CourseFactory.create(**self.course_options())  # pylint: disable=attribute-defined-outside-init
            chapter = ItemFactory.create(parent=self.course, category='chapter')
            self.html_block = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=chapter,
                category='html',
                data="<p>Test HTML Content<p>"
            )

    def setup_user(self, admin=False, enroll=False, login=False):
        """
        Helper method to create the user.
        """
        self.user = AdminFactory() if admin else UserFactory()  # pylint: disable=attribute-defined-outside-init

        if enroll:
            CourseEnrollmentFactory(user=self.user, course_id=self.course.id)

        if login:
            self.login()

    def verify_response(self, expected_response_code=200, url_params=None):
        """
        Helper method that calls the endpoint, verifies the expected response code, and returns the response.
        """
        if url_params:
            url_params = urlencode(url_params)
        response = self.get_response(url_params)
        if expected_response_code == 200:
            self.assertContains(response, self.html_block.data, status_code=expected_response_code)
            for chrome_element in [self.COURSEWARE_CHROME_HTML_ELEMENTS + self.XBLOCK_REMOVED_HTML_ELEMENTS]:
                self.assertNotContains(response, chrome_element)
        else:
            self.assertNotContains(response, self.html_block.data, status_code=expected_response_code)
        return response

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 7),
        (ModuleStoreEnum.Type.split, 5),
    )
    @ddt.unpack
    def test_courseware_html(self, default_store, mongo_calls):
        """
        To verify that the removal of courseware chrome elements is working,
        we include this test here to make sure the chrome elements that should
        be removed actually exist in the full courseware page.
        If this test fails, it's probably because the HTML template for courseware
        has changed and COURSEWARE_CHROME_HTML_ELEMENTS needs to be updated.
        """
        with self.store.default_store(default_store):
            self.setup_course(default_store)
            self.setup_user(admin=True, enroll=True, login=True)

            with check_mongo_calls(mongo_calls):
                url = get_redirect_url(self.course.id, self.html_block.location)
                response = self.client.get(url)
                for chrome_element in self.COURSEWARE_CHROME_HTML_ELEMENTS:
                    self.assertContains(response, chrome_element)

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 6),
        (ModuleStoreEnum.Type.split, 5),
    )
    @ddt.unpack
    def test_success_enrolled_staff(self, default_store, mongo_calls):
        with self.store.default_store(default_store):
            self.setup_course(default_store)
            self.setup_user(admin=True, enroll=True, login=True)

            # The 5 mongoDB calls include calls for
            # Old Mongo:
            #   (1) fill_in_run
            #   (2) get_course in get_course_with_access
            #   (3) get_item for HTML block in get_module_by_usage_id
            #   (4) get_parent when loading HTML block
            #   (5) edx_notes descriptor call to get_course
            #   (6) get_course in handle_progress_event
            # Split:
            #   (1) course_index - bulk_operation call
            #   (2) structure - get_course_with_access
            #   (3) definition - get_course_with_access
            #   (4) definition - HTML block
            #   (5) definition - edx_notes decorator (original_get_html)
            with check_mongo_calls(mongo_calls):
                self.verify_response()

    def test_success_unenrolled_staff(self):
        self.setup_course()
        self.setup_user(admin=True, enroll=False, login=True)
        self.verify_response()

    def test_success_enrolled_student(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=True)
        self.verify_response()

    def test_unauthenticated(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=False)
        self.verify_response(expected_response_code=404)

    def test_unenrolled_student(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=False, login=True)
        self.verify_response(expected_response_code=404)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_fail_block_unreleased(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=True)
        self.html_block.start = datetime.max
        modulestore().update_item(self.html_block, self.user.id)
        self.verify_response(expected_response_code=404)

    def test_fail_block_nonvisible(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=True)
        self.html_block.visible_to_staff_only = True
        modulestore().update_item(self.html_block, self.user.id)
        self.verify_response(expected_response_code=404)

    def test_student_view_param(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=True)
        self.verify_response(url_params={'view': 'student_view'})

    def test_unsupported_view_param(self):
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=True)
        self.verify_response(url_params={'view': 'author_view'}, expected_response_code=400)


class FieldOverrideTestMixin(object):
    """
    A Mixin helper class for classes that test Field Overrides.
    """
    def setUp(self):
        super(FieldOverrideTestMixin, self).setUp()
        OverrideModulestoreFieldData.provider_classes = None

    def tearDown(self):
        super(FieldOverrideTestMixin, self).tearDown()
        OverrideModulestoreFieldData.provider_classes = None
