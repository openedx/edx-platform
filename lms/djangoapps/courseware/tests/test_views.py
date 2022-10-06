"""
Tests courseware views.py
"""

import html
import itertools
import json
import re
from datetime import datetime, timedelta
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch
from urllib.parse import quote, urlencode
from uuid import uuid4

import ddt
from completion.test_utils import CompletionWaffleTestMixin
from crum import set_current_request
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.http.request import QueryDict
from django.test import RequestFactory, TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.urls import reverse, reverse_lazy
from edx_toggles.toggles.testutils import override_waffle_flag
from freezegun import freeze_time
from opaque_keys.edx.keys import CourseKey, UsageKey
from pytz import UTC
from rest_framework import status
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String
from xmodule.capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from xmodule.data import CertificatesDisplayBehaviors
from xmodule.graders import ShowCorrectness
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import CourseUserType, ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

import lms.djangoapps.courseware.views.views as views
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseStaffRole
from common.djangoapps.student.tests.factories import (
    TEST_PASSWORD,
    AdminFactory,
    CourseEnrollmentFactory,
    GlobalStaffFactory,
    RequestFactoryNoCsrf,
    UserFactory
)
from common.djangoapps.util.tests.test_date_utils import fake_pgettext, fake_ugettext
from common.djangoapps.util.url import reload_django_url_config
from common.djangoapps.util.views import ensure_valid_course_key
from lms.djangoapps.certificates import api as certs_api
from lms.djangoapps.certificates.models import (
    CertificateGenerationConfiguration,
    CertificateGenerationCourseSetting,
    CertificateStatuses
)
from lms.djangoapps.certificates.tests.factories import (
    CertificateAllowlistFactory,
    CertificateInvalidationFactory,
    GeneratedCertificateFactory
)
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.courseware.access_utils import check_course_open_for_learner
from lms.djangoapps.courseware.model_data import FieldDataCache, set_score
from lms.djangoapps.courseware.module_render import get_module, handle_xblock_callback
from lms.djangoapps.courseware.tests.factories import StudentModuleFactory
from lms.djangoapps.courseware.tests.helpers import MasqueradeMixin, get_expiration_banner_text, set_preview_mode
from lms.djangoapps.courseware.testutils import RenderXBlockTestMixin
from lms.djangoapps.courseware.toggles import COURSEWARE_OPTIMIZED_RENDER_XBLOCK
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from lms.djangoapps.instructor.access import allow_access
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory as CatalogCourseFactory
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory, ProgramFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.crawlers.models import CrawlersConfig
from openedx.core.djangoapps.credit.api import set_credit_requirements
from openedx.core.djangoapps.credit.models import CreditCourse, CreditProvider
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.djangolib.testing.utils import get_mock_request
from openedx.core.lib.url_utils import quote_slashes
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.course_experience import (
    DISABLE_COURSE_OUTLINE_PAGE_FLAG,
)
from openedx.features.course_experience.tests.views.helpers import add_course_mode
from openedx.features.course_experience.url_helpers import (
    get_courseware_url,
    get_learning_mfe_home_url,
    make_learning_mfe_courseware_url
)
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseTestConsentRequired

QUERY_COUNT_TABLE_IGNORELIST = WAFFLE_TABLES

FEATURES_WITH_DISABLE_HONOR_CERTIFICATE = settings.FEATURES.copy()
FEATURES_WITH_DISABLE_HONOR_CERTIFICATE['DISABLE_HONOR_CERTIFICATES'] = True


@ddt.ddt
class TestJumpTo(ModuleStoreTestCase):
    """
    Check the jumpto link for a course.
    """
    @ddt.data(
        (True, False),  # preview -> Legacy experience
        (False, True),  # no preview -> MFE experience
    )
    @ddt.unpack
    def test_jump_to_legacy_vs_mfe(self, preview_mode, expect_mfe):
        """
        Test that jump_to and jump_to_id correctly choose which courseware frontend to redirect to.

        Can be removed when the MFE supports a preview mode.
        """
        course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        if expect_mfe:
            expected_url = f'http://learning-mfe/course/{course.id}/{chapter.location}'
        else:
            expected_url = f'/courses/{course.id}/courseware/{chapter.url_name}/'

        jumpto_url = f'/courses/{course.id}/jump_to/{chapter.location}'
        with set_preview_mode(preview_mode):
            response = self.client.get(jumpto_url)
        assert response.status_code == 302
        # Check the response URL, but chop off the querystring; we don't care here.
        assert response.url.split('?')[0] == expected_url

        jumpto_id_url = f'/courses/{course.id}/jump_to_id/{chapter.url_name}'
        with set_preview_mode(preview_mode):
            response = self.client.get(jumpto_id_url)
        assert response.status_code == 302
        # Check the response URL, but chop off the querystring; we don't care here.
        assert response.url.split('?')[0] == expected_url

    @ddt.data(
        (False, ModuleStoreEnum.Type.mongo),
        (False, ModuleStoreEnum.Type.split),
        (True, ModuleStoreEnum.Type.split),
    )
    @ddt.unpack
    def test_jump_to_invalid_location(self, preview_mode, store_type):
        """Confirm that invalid locations redirect back to a general course URL"""
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            location = course.id.make_usage_key(None, 'NoSuchPlace')
        expected_redirect_url = (
            f'/courses/{course.id}/courseware?' + urlencode({'activate_block_id': str(course.location)})
        ) if preview_mode else (
            f'http://learning-mfe/course/{course.id}'
        )
        # This is fragile, but unfortunately the problem is that within the LMS we
        # can't use the reverse calls from the CMS
        jumpto_url = f'/courses/{course.id}/jump_to/{location}'
        with set_preview_mode(preview_mode):
            response = self.client.get(jumpto_url)
        assert response.status_code == 302
        assert response.url == expected_redirect_url

    @set_preview_mode(True)
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_jump_to_legacy_from_sequence(self, store_type):
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequence = ItemFactory.create(category='sequential', parent_location=chapter.location)
        activate_block_id = urlencode({'activate_block_id': str(sequence.location)})
        expected_redirect_url = (
            f'/courses/{course.id}/courseware/{chapter.url_name}/{sequence.url_name}/?{activate_block_id}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{sequence.location}'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=302)

    @set_preview_mode(False)
    def test_jump_to_mfe_from_sequence(self):
        course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        sequence = ItemFactory.create(category='sequential', parent_location=chapter.location)
        expected_redirect_url = (
            f'http://learning-mfe/course/{course.id}/{sequence.location}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{sequence.location}'
        response = self.client.get(jumpto_url)
        assert response.status_code == 302
        assert response.url == expected_redirect_url

    @set_preview_mode(True)
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_jump_to_legacy_from_module(self, store_type):
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequence = ItemFactory.create(category='sequential', parent_location=chapter.location)
            vertical1 = ItemFactory.create(category='vertical', parent_location=sequence.location)
            vertical2 = ItemFactory.create(category='vertical', parent_location=sequence.location)
            module1 = ItemFactory.create(category='html', parent_location=vertical1.location)
            module2 = ItemFactory.create(category='html', parent_location=vertical2.location)

        activate_block_id = urlencode({'activate_block_id': str(module1.location)})
        expected_redirect_url = (
            f'/courses/{course.id}/courseware/{chapter.url_name}/{sequence.url_name}/1?{activate_block_id}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{module1.location}'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=302)

        activate_block_id = urlencode({'activate_block_id': str(module2.location)})
        expected_redirect_url = (
            f'/courses/{course.id}/courseware/{chapter.url_name}/{sequence.url_name}/2?{activate_block_id}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{module2.location}'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=302)

    @set_preview_mode(False)
    def test_jump_to_mfe_from_module(self):
        course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent_location=course.location)
        sequence = ItemFactory.create(category='sequential', parent_location=chapter.location)
        vertical1 = ItemFactory.create(category='vertical', parent_location=sequence.location)
        vertical2 = ItemFactory.create(category='vertical', parent_location=sequence.location)
        module1 = ItemFactory.create(category='html', parent_location=vertical1.location)
        module2 = ItemFactory.create(category='html', parent_location=vertical2.location)

        expected_redirect_url = (
            f'http://learning-mfe/course/{course.id}/{sequence.location}/{vertical1.location}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{module1.location}'
        response = self.client.get(jumpto_url)
        assert response.status_code == 302
        assert response.url == expected_redirect_url

        expected_redirect_url = (
            f'http://learning-mfe/course/{course.id}/{sequence.location}/{vertical2.location}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{module2.location}'
        response = self.client.get(jumpto_url)
        assert response.status_code == 302
        assert response.url == expected_redirect_url

    # The new courseware experience does not support this sort of course structure;
    # it assumes a simple course->chapter->sequence->unit->component tree.
    @set_preview_mode(True)
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_jump_to_legacy_from_nested_module(self, store_type):
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequence = ItemFactory.create(category='sequential', parent_location=chapter.location)
            vertical = ItemFactory.create(category='vertical', parent_location=sequence.location)
            nested_sequence = ItemFactory.create(category='sequential', parent_location=vertical.location)
            nested_vertical1 = ItemFactory.create(category='vertical', parent_location=nested_sequence.location)
            # put a module into nested_vertical1 for completeness
            ItemFactory.create(category='html', parent_location=nested_vertical1.location)
            nested_vertical2 = ItemFactory.create(category='vertical', parent_location=nested_sequence.location)
            module2 = ItemFactory.create(category='html', parent_location=nested_vertical2.location)

        # internal position of module2 will be 1_2 (2nd item withing 1st item)
        activate_block_id = urlencode({'activate_block_id': str(module2.location)})
        expected_redirect_url = (
            f'/courses/{course.id}/courseware/{chapter.url_name}/{sequence.url_name}/1?{activate_block_id}'
        )
        jumpto_url = f'/courses/{course.id}/jump_to/{module2.location}'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=302)

    @ddt.data(
        (False, ModuleStoreEnum.Type.mongo),
        (False, ModuleStoreEnum.Type.split),
        (True, ModuleStoreEnum.Type.split),
    )
    @ddt.unpack
    def test_jump_to_id_invalid_location(self, preview_mode, store_type):
        with self.store.default_store(store_type):
            course = CourseFactory.create()
        jumpto_url = f'/courses/{course.id}/jump_to/NoSuchPlace'
        with set_preview_mode(preview_mode):
            response = self.client.get(jumpto_url)
        assert response.status_code == 404

    @set_preview_mode(True)
    @ddt.data(
        (ModuleStoreEnum.Type.mongo, False, '1'),
        (ModuleStoreEnum.Type.mongo, True, '2'),
        (ModuleStoreEnum.Type.split, False, '1'),
        (ModuleStoreEnum.Type.split, True, '2'),
    )
    @ddt.unpack
    def test_jump_to_legacy_for_learner_with_staff_only_content(self, store_type, is_staff_user, position):
        """
        Test for checking correct position in redirect_url for learner when a course has staff-only units.

        (When the MFE is active, it handles this logic itself with the help of the
         courseware blocks/metadata/outline APIs, so we don't test for it here.)
        """
        with self.store.default_store(store_type):
            course = CourseFactory.create()
            request = RequestFactory().get('/')
            request.user = UserFactory(is_staff=is_staff_user, username="staff")
            request.session = {}
            course_key = CourseKey.from_string(str(course.id))
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequence = ItemFactory.create(category='sequential', parent_location=chapter.location)
            __ = ItemFactory.create(category='vertical', parent_location=sequence.location)
            staff_only_vertical = ItemFactory.create(category='vertical', parent_location=sequence.location,
                                                     metadata=dict(visible_to_staff_only=True))
            __ = ItemFactory.create(category='vertical', parent_location=sequence.location)

        usage_key = UsageKey.from_string(str(staff_only_vertical.location)).replace(course_key=course_key)
        expected_url = reverse(
            'courseware_position',
            kwargs={
                'course_id': str(course.id),
                'chapter': chapter.url_name,
                'section': sequence.url_name,
                'position': position,
            }
        )
        expected_url += "?{}".format(urlencode({'activate_block_id': str(staff_only_vertical.location)}))
        assert expected_url == get_courseware_url(usage_key, request)


@set_preview_mode(True)
class IndexQueryTestCase(ModuleStoreTestCase):
    """
    Tests for query count.
    """
    NUM_PROBLEMS = 20

    @patch('common.djangoapps.student.helpers.get_course_dates_for_email')
    def test_index_query_counts(self, mock_course_dates_for_email):
        # TODO: decrease query count as part of REVO-28
        mock_course_dates_for_email.return_value = []
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        with self.store.default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()
            with self.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                vertical = ItemFactory.create(category='vertical', parent_location=section.location)
                for _ in range(self.NUM_PROBLEMS):
                    ItemFactory.create(category='problem', parent_location=vertical.location)

        course_run = CourseRunFactory.create(key=course.id)
        course_run['title'] = course.display_name
        course_run['short_description'] = None
        course_run['marketing_url'] = 'www.edx.org'
        course_run['pacing_type'] = 'self_paced'
        course_run['banner_image_url'] = ''
        course_run['min_effort'] = 1
        course_run['enrollment_count'] = 12345

        patch_course_data = patch('openedx.core.djangoapps.catalog.api.get_course_run_details')
        course_data = patch_course_data.start()
        course_data.return_value = course_run
        self.addCleanup(patch_course_data.stop)

        self.client.login(username=self.user.username, password=self.user_password)
        CourseEnrollment.enroll(self.user, course.id)

        with self.assertNumQueries(202, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST):
            with check_mongo_calls(3):
                url = reverse(
                    'courseware_section',
                    kwargs={
                        'course_id': str(course.id),
                        'chapter': str(chapter.location.block_id),
                        'section': str(section.location.block_id),
                    }
                )
                response = self.client.get(url)
                assert response.status_code == 200


class BaseViewsTestCase(ModuleStoreTestCase, MasqueradeMixin):
    """Base class for courseware tests"""
    CREATE_USER = False

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(display_name='teꜱᴛ course', run="Testing_course")
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                category='chapter',
                parent_location=self.course.location,
                display_name="Chapter 1",
            )
            self.section = ItemFactory.create(
                category='sequential',
                parent_location=self.chapter.location,
                due=datetime(2013, 9, 18, 11, 30, 00),
                display_name='Sequential 1',
                format='Homework'
            )
            self.vertical = ItemFactory.create(
                category='vertical',
                parent_location=self.section.location,
                display_name='Vertical 1',
            )
            self.problem = ItemFactory.create(
                category='problem',
                parent_location=self.vertical.location,
                display_name='Problem 1',
            )

            self.section2 = ItemFactory.create(
                category='sequential',
                parent_location=self.chapter.location,
                display_name='Sequential 2',
            )
            self.vertical2 = ItemFactory.create(
                category='vertical',
                parent_location=self.section2.location,
                display_name='Vertical 2',
            )
            self.problem2 = ItemFactory.create(
                category='problem',
                parent_location=self.vertical2.location,
                display_name='Problem 2',
            )

        self.course_key = self.course.id
        # Set profile country to Åland Islands to check Unicode characters does not raise error
        self.user = UserFactory(username='dummy', profile__country='AX')
        self.date = datetime(2013, 1, 22, tzinfo=UTC)
        self.enrollment = CourseEnrollment.enroll(self.user, self.course_key)
        self.enrollment.created = self.date
        self.enrollment.save()
        chapter = 'Overview'
        self.chapter_url = '{}/{}/{}'.format('/courses', self.course_key, chapter)

        self.org = "ꜱᴛᴀʀᴋ ɪɴᴅᴜꜱᴛʀɪᴇꜱ"
        self.org_html = "<p>'+Stark/Industries+'</p>"

        assert self.client.login(username=self.user.username, password=TEST_PASSWORD)

        # refresh the course from the modulestore so that it has children
        self.course = modulestore().get_course(self.course.id)

    def _create_global_staff_user(self):
        """
        Create global staff user and log them in
        """
        self.global_staff = GlobalStaffFactory.create()  # pylint: disable=attribute-defined-outside-init
        assert self.client.login(username=self.global_staff.username, password=TEST_PASSWORD)

    def _get_urls(self):  # lint-amnesty, pylint: disable=missing-function-docstring
        lms_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course_key),
                'chapter': str(self.chapter.location.block_id),
                'section': str(self.section2.location.block_id),
            },
        ) + '?foo=b$r'
        mfe_url = '{}/course/{}/{}?foo=b%24r'.format(
            settings.LEARNING_MICROFRONTEND_URL,
            self.course_key,
            self.section2.location
        )
        preview_url = "http://" + settings.FEATURES.get('PREVIEW_LMS_BASE') + lms_url

        return lms_url, mfe_url, preview_url


@ddt.ddt
@set_preview_mode(True)
class CoursewareIndexTestCase(BaseViewsTestCase):
    """
    Tests for the courseware index view, used for instructor previews.
    """
    def setUp(self):
        super().setUp()
        self._create_global_staff_user()  # this view needs staff permission

    def test_index_success(self):
        response = self._verify_index_response()
        self.assertContains(response, self.problem2.location.replace(branch=None, version_guid=None))

        # re-access to the main course page redirects to last accessed view.
        url = reverse('courseware', kwargs={'course_id': str(self.course_key)})
        response = self.client.get(url)
        assert response.status_code == 302
        response = self.client.get(response.url)
        self.assertNotContains(response, self.problem.location.replace(branch=None, version_guid=None))
        self.assertContains(response, self.problem2.location.replace(branch=None, version_guid=None))

    @set_preview_mode(True)
    def test_index_nonexistent_chapter(self):
        self._verify_index_response(expected_response_code=404, chapter_name='non-existent')

    def test_index_nonexistent_chapter_masquerade(self):
        self.update_masquerade(username=self.user.username)
        self._verify_index_response(expected_response_code=302, chapter_name='non-existent')

    def test_index_nonexistent_section(self):
        self._verify_index_response(expected_response_code=404, section_name='non-existent')

    def test_index_nonexistent_section_masquerade(self):
        self.update_masquerade(username=self.user.username)
        self._verify_index_response(expected_response_code=302, section_name='non-existent')

    def _verify_index_response(self, expected_response_code=200, chapter_name=None, section_name=None):
        """
        Verifies the response when the courseware index page is accessed with
        the given chapter and section names.
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course_key),
                'chapter': str(self.chapter.location.block_id) if chapter_name is None else chapter_name,
                'section': str(self.section2.location.block_id) if section_name is None else section_name,
            }
        )
        response = self.client.get(url)
        assert response.status_code == expected_response_code
        return response

    def test_get_redirect_url(self):
        # test the course location
        assert '/courses/{course_key}/courseware?{activate_block_id}'.format(
            course_key=str(self.course_key),
            activate_block_id=urlencode({'activate_block_id': str(self.course.location)})
        ) == get_courseware_url(self.course.location)
        # test a section location
        assert '/courses/{course_key}/courseware/Chapter_1/Sequential_1/?{activate_block_id}'.format(
            course_key=str(self.course_key),
            activate_block_id=urlencode({'activate_block_id': str(self.section.location)})
        ) == get_courseware_url(self.section.location)

    def test_index_invalid_position(self):
        request_url = '/'.join([
            '/courses',
            str(self.course.id),
            'courseware',
            self.chapter.location.block_id,
            self.section.location.block_id,
            'f'
        ])
        response = self.client.get(request_url)
        assert response.status_code == 404

    def test_unicode_handling_in_url(self):
        url_parts = [
            '/courses',
            str(self.course.id),
            'courseware',
            self.chapter.location.block_id,
            self.section.location.block_id,
            '1'
        ]
        for idx, val in enumerate(url_parts):
            url_parts_copy = url_parts[:]
            url_parts_copy[idx] = val + 'χ'
            request_url = '/'.join(url_parts_copy)
            response = self.client.get(request_url)
            assert response.status_code == 404

    # TODO: TNL-6387: Remove test
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_accordion(self):
        """
        This needs a response_context, which is not included in the render_accordion's main method
        returning a render_to_string, so we will render via the courseware URL in order to include
        the needed context
        """
        response = self.client.get(
            reverse('courseware', args=[str(self.course.id)]),
            follow=True
        )
        test_responses = [
            '<p class="accordion-display-name">Sequential 1 <span class="sr">current section</span></p>',
            '<p class="accordion-display-name">Sequential 2 </p>'
        ]
        for test in test_responses:
            self.assertContains(response, test)


@ddt.ddt
class ViewsTestCase(BaseViewsTestCase):
    """
    Tests for views.py methods.
    """
    YESTERDAY = 'yesterday'
    DATES = {
        YESTERDAY: datetime.now(UTC) - timedelta(days=1),
        None: None,
    }

    def test_mfe_link_from_about_page(self):
        """
        Verify course about page links to the MFE.
        """
        with self.store.default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()
        CourseEnrollment.enroll(self.user, course.id)

        response = self.client.get(reverse('about_course', args=[str(course.id)]))
        self.assertContains(response, get_learning_mfe_home_url(course_key=course.id, url_fragment='home'))

    def _create_url_for_enroll_staff(self):
        """
        creates the courseware url and enroll staff url
        """
        # create the _next parameter
        courseware_url = make_learning_mfe_courseware_url(self.course.id, self.chapter.location, self.section.location)
        courseware_url = quote(courseware_url, safe=':/')
        # create the url for enroll_staff view
        enroll_url = "{enroll_url}?next={courseware_url}".format(
            enroll_url=reverse('enroll_staff', kwargs={'course_id': str(self.course.id)}),
            courseware_url=courseware_url
        )
        return courseware_url, enroll_url

    @ddt.data(
        ({'enroll': "Enroll"}, True),
        ({'dont_enroll': "Don't enroll"}, False))
    @ddt.unpack
    def test_enroll_staff_redirection(self, data, enrollment):
        """
        Verify unenrolled staff is redirected to correct url.
        """
        self._create_global_staff_user()
        courseware_url, enroll_url = self._create_url_for_enroll_staff()
        response = self.client.post(enroll_url, data=data)

        # we were redirected to our current location
        if enrollment:
            self.assertRedirects(response, courseware_url, fetch_redirect_response=False)
        else:
            self.assertRedirects(response, f'/courses/{str(self.course_key)}/about')

    def test_enroll_staff_with_invalid_data(self):
        """
        If we try to post with an invalid data pattern, then we'll redirected to
        course about page.
        """
        self._create_global_staff_user()
        __, enroll_url = self._create_url_for_enroll_staff()
        response = self.client.post(enroll_url, data={'test': "test"})
        assert response.status_code == 302
        self.assertRedirects(response, f'/courses/{str(self.course_key)}/about')

    def assert_enrollment_link_present(self, is_anonymous):
        """
        Prepare ecommerce checkout data and assert if the ecommerce link is contained in the response.
        Arguments:
            is_anonymous(bool): Tell the method to use an anonymous user or the logged in one.
            _id(bool): Tell the method to either expect an id in the href or not.
        """
        sku = 'TEST123'
        configuration = CommerceConfiguration.objects.create(checkout_on_ecommerce_service=True)
        course = CourseFactory.create()
        CourseModeFactory(mode_slug=CourseMode.PROFESSIONAL, course_id=course.id, sku=sku, min_price=1)

        if is_anonymous:
            self.client.logout()
        else:
            assert self.client.login(username=self.user.username, password=TEST_PASSWORD)

        # Construct the link according the following scenarios and verify its presence in the response:
        #      (1) shopping cart is enabled and the user is not logged in
        #      (2) shopping cart is enabled and the user is logged in
        href = '<a href="{uri_stem}?sku={sku}" class="add-to-cart">'.format(
            uri_stem=configuration.basket_checkout_page,
            sku=sku,
        )

        # Generate the course about page content
        response = self.client.get(reverse('about_course', args=[str(course.id)]))
        self.assertContains(response, href)

    @ddt.data(True, False)
    def test_ecommerce_checkout(self, is_anonymous):
        if not is_anonymous:
            self.assert_enrollment_link_present(is_anonymous=is_anonymous)
        else:
            assert EcommerceService().is_enabled(AnonymousUser()) is False

    def test_user_groups(self):
        # deprecated function
        mock_user = MagicMock()
        type(mock_user).is_authenticated = PropertyMock(return_value=False)
        assert views.user_groups(mock_user) == []

    def test_invalid_course_id(self):
        response = self.client.get('/courses/MITx/3.091X/')
        assert response.status_code == 404

    def test_incomplete_course_id(self):
        response = self.client.get('/courses/MITx/')
        assert response.status_code == 404

    def test_jump_to_invalid(self):
        # TODO add a test for invalid location
        # TODO add a test for no data *
        response = self.client.get(reverse('jump_to', args=['foo/bar/baz', 'baz']))
        assert response.status_code == 404

    def verify_end_date(self, course_id, expected_end_text=None):
        """
        Visits the about page for `course_id` and tests that both the text "Classes End", as well
        as the specified `expected_end_text`, is present on the page.
        If `expected_end_text` is None, verifies that the about page *does not* contain the text
        "Classes End".
        """
        result = self.client.get(reverse('about_course', args=[str(course_id)]))
        if expected_end_text is not None:
            self.assertContains(result, "Classes End")
            self.assertContains(result, expected_end_text)
        else:
            self.assertNotContains(result, "Classes End")

    def test_submission_history_accepts_valid_ids(self):
        # log into a staff account
        admin = AdminFactory()

        assert self.client.login(username=admin.username, password='test')

        url = reverse('submission_history', kwargs={
            'course_id': str(self.course_key),
            'learner_identifier': 'dummy',
            'location': str(self.problem.location),
        })
        response = self.client.get(url)
        # Tests that we do not get an "Invalid x" response when passing correct arguments to view
        self.assertNotContains(response, 'Invalid')

    def test_submission_history_xss(self):
        # log into a staff account
        admin = AdminFactory()

        assert self.client.login(username=admin.username, password='test')

        # try it with an existing user and a malicious location
        url = reverse('submission_history', kwargs={
            'course_id': str(self.course_key),
            'learner_identifier': 'dummy',
            'location': '<script>alert("hello");</script>'
        })
        response = self.client.get(url)
        self.assertNotContains(response, '<script>')

        # try it with a malicious user and a non-existent location
        url = reverse('submission_history', kwargs={
            'course_id': str(self.course_key),
            'learner_identifier': '<script>alert("hello");</script>',
            'location': 'dummy'
        })
        response = self.client.get(url)
        self.assertNotContains(response, '<script>')

    def test_submission_history_contents(self):
        # log into a staff account
        admin = AdminFactory.create()

        assert self.client.login(username=admin.username, password='test')

        usage_key = self.course_key.make_usage_key('problem', 'test-history')
        state_client = DjangoXBlockUserStateClient(admin)

        # store state via the UserStateClient
        state_client.set(
            username=admin.username,
            block_key=usage_key,
            state={'field_a': 'x', 'field_b': 'y'}
        )

        set_score(admin.id, usage_key, 0, 3)

        state_client.set(
            username=admin.username,
            block_key=usage_key,
            state={'field_a': 'a', 'field_b': 'b'}
        )
        set_score(admin.id, usage_key, 3, 3)

        url = reverse('submission_history', kwargs={
            'course_id': str(self.course_key),
            'learner_identifier': admin.email,
            'location': str(usage_key),
        })
        response = self.client.get(url)
        response_content = html.unescape(response.content.decode('utf-8'))

        # We have update the state 4 times: twice to change content, and twice
        # to set the scores. We'll check that the identifying content from each is
        # displayed (but not the order), and also the indexes assigned in the output
        # #1 - #4

        assert '#1' in response_content
        assert json.dumps({'field_a': 'a', 'field_b': 'b'}, sort_keys=True, indent=2) in response_content
        assert 'Score: 0.0 / 3.0' in response_content
        assert json.dumps({'field_a': 'x', 'field_b': 'y'}, sort_keys=True, indent=2) in response_content
        assert 'Score: 3.0 / 3.0' in response_content
        assert '#4' in response_content

    @ddt.data(('America/New_York', -5),  # UTC - 5
              ('Asia/Pyongyang', 9),  # UTC + 9
              ('Europe/London', 0),  # UTC
              ('Canada/Yukon', -8),  # UTC - 8
              ('Europe/Moscow', 4))  # UTC + 3 + 1 for daylight savings
    @ddt.unpack
    def test_submission_history_timezone(self, timezone, hour_diff):
        with freeze_time('2012-01-01'):
            with (override_settings(TIME_ZONE=timezone)):  # lint-amnesty, pylint: disable=superfluous-parens
                course = CourseFactory.create()
                course_key = course.id
                client = Client()
                admin = AdminFactory.create()
                assert client.login(username=admin.username, password='test')
                state_client = DjangoXBlockUserStateClient(admin)
                usage_key = course_key.make_usage_key('problem', 'test-history')
                state_client.set(
                    username=admin.username,
                    block_key=usage_key,
                    state={'field_a': 'x', 'field_b': 'y'}
                )
                url = reverse('submission_history', kwargs={
                    'course_id': str(course_key),
                    'learner_identifier': admin.username,
                    'location': str(usage_key),
                })
                response = client.get(url)
                expected_time = datetime.now() + timedelta(hours=hour_diff)
                expected_tz = expected_time.strftime('%Z')
                self.assertContains(response, expected_tz)
                self.assertContains(response, str(expected_time))

    def _email_opt_in_checkbox(self, response, org_name_string=None):
        """Check if the email opt-in checkbox appears in the response content."""
        checkbox_html = '<input id="email-opt-in" type="checkbox" name="opt-in" class="email-opt-in" value="true" checked>'  # lint-amnesty, pylint: disable=line-too-long
        if org_name_string:
            # Verify that the email opt-in checkbox appears, and that the expected
            # organization name is displayed.
            self.assertContains(response, checkbox_html, html=True)
            self.assertContains(response, org_name_string)
        else:
            # Verify that the email opt-in checkbox does not appear
            self.assertNotContains(response, checkbox_html, html=True)

    def test_financial_assistance_page(self):
        url = reverse('financial_assistance')
        response = self.client.get(url)
        # This is a static page, so just assert that it is returned correctly
        assert response.status_code == 200
        self.assertContains(response, 'Financial Assistance Application')

    @patch('lms.djangoapps.courseware.views.views._use_new_financial_assistance_flow', return_value=True)
    @patch('lms.djangoapps.courseware.views.views.is_eligible_for_financial_aid', return_value=(False, 'error reason'))
    def test_new_financial_assistance_page_course_ineligible(self, *args):
        """
        Test to verify the financial_assistance view against an ineligible course returns an error page.
        """
        url = reverse('financial_assistance_v2', args=['course-v1:test+TestX+Test_Course'])
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertContains(response, 'This course is not eligible for Financial Assistance for the following reason:')

    @ddt.data(([CourseMode.AUDIT, CourseMode.VERIFIED], CourseMode.AUDIT, True, YESTERDAY),
              ([CourseMode.AUDIT, CourseMode.VERIFIED], CourseMode.VERIFIED, True, None),
              ([CourseMode.AUDIT, CourseMode.VERIFIED], CourseMode.AUDIT, False, None),
              ([CourseMode.AUDIT], CourseMode.AUDIT, False, None))
    @ddt.unpack
    def test_financial_assistance_form_course_exclusion(
            self, course_modes, enrollment_mode, eligible_for_aid, expiration):
        """Verify that learner cannot get the financial aid for the courses having one of the
        following attributes:
        1. User is enrolled in the verified mode.
        2. Course is expired.
        3. Course does not provide financial assistance.
        4. Course does not have verified mode.
        """
        # Create course
        course = CourseFactory.create()

        # Create Course Modes
        for mode in course_modes:
            CourseModeFactory.create(mode_slug=mode, course_id=course.id, expiration_datetime=self.DATES[expiration])

        # Enroll user in the course
        CourseEnrollmentFactory(course_id=course.id, user=self.user, mode=enrollment_mode)
        # load course into course overview
        CourseOverview.get_from_id(course.id)

        # add whether course is eligible for financial aid or not
        course_overview = CourseOverview.objects.get(id=course.id)
        course_overview.eligible_for_financial_aid = eligible_for_aid
        course_overview.save()

        url = reverse('financial_assistance_form')
        response = self.client.get(url)
        assert response.status_code == 200

        self.assertNotContains(response, str(course.id))

    def test_financial_assistance_form(self):
        """Verify that learner can get the financial aid for the course in which
        he/she is enrolled in audit mode whereas the course provide verified mode.
        """
        # Create course
        course = CourseFactory.create().id

        # Create Course Modes
        CourseModeFactory.create(mode_slug=CourseMode.AUDIT, course_id=course)
        CourseModeFactory.create(mode_slug=CourseMode.VERIFIED, course_id=course)

        # Enroll user in the course
        CourseEnrollmentFactory(course_id=course, user=self.user, mode=CourseMode.AUDIT)
        # load course into course overview
        CourseOverview.get_from_id(course)

        url = reverse('financial_assistance_form')
        response = self.client.get(url)
        assert response.status_code == 200

        self.assertContains(response, str(course))

    def _submit_financial_assistance_form(self, data, submit_url='submit_financial_assistance_request',
                                          referrer_url=None):
        """Submit a financial assistance request."""
        url = reverse(submit_url)
        return self.client.post(url, json.dumps(data), content_type='application/json', HTTP_REFERER=referrer_url)

    @patch.object(views, 'create_zendesk_ticket', return_value=200)
    def test_submit_financial_assistance_request(self, mock_create_zendesk_ticket):
        username = self.user.username
        course = str(self.course_key)
        legal_name = 'Jesse Pinkman'
        country = 'United States'
        income = '1234567890'
        reason_for_applying = "It's just basic chemistry, yo."
        goals = "I don't know if it even matters, but... work with my hands, I guess."
        effort = "I'm done, okay? You just give me my money, and you and I, we're done."
        data = {
            'username': username,
            'course': course,
            'name': legal_name,
            'email': self.user.email,
            'country': country,
            'income': income,
            'reason_for_applying': reason_for_applying,
            'goals': goals,
            'effort': effort,
            'mktg-permission': False,
        }
        response = self._submit_financial_assistance_form(data)
        assert response.status_code == 204

        __, __, ticket_subject, __ = mock_create_zendesk_ticket.call_args[0]
        mocked_kwargs = mock_create_zendesk_ticket.call_args[1]
        group_name = mocked_kwargs['group']
        tags = mocked_kwargs['tags']
        additional_info = mocked_kwargs['additional_info']

        private_comment = '\n'.join(list(additional_info.values()))
        for info in (country, income, reason_for_applying, goals, effort, username, legal_name, course):
            assert info in private_comment

        assert additional_info['Allowed for marketing purposes'] == 'No'

        assert ticket_subject == f'Financial assistance request for learner {username} in course {self.course.display_name}'  # pylint: disable=line-too-long
        self.assertDictContainsSubset({'course_id': course}, tags)
        assert 'Client IP' in additional_info
        assert group_name == 'Financial Assistance'

    @patch.object(views, 'create_zendesk_ticket', return_value=500)
    def test_zendesk_submission_failed(self, _mock_create_zendesk_ticket):
        response = self._submit_financial_assistance_form({
            'username': self.user.username,
            'course': str(self.course.id),
            'name': '',
            'email': '',
            'country': '',
            'income': '',
            'reason_for_applying': '',
            'goals': '',
            'effort': '',
            'mktg-permission': False,
        })
        assert response.status_code == 500

    @patch.object(
        views, 'create_financial_assistance_application', return_value=HttpResponse(status=status.HTTP_204_NO_CONTENT)
    )
    @ddt.data(
        ('/financial-assistance/course-v1:test+TestX+Test_Course/apply/', status.HTTP_204_NO_CONTENT),
        ('/financial-assistance/course-v1:invalid+ErrorX+Invalid_Course/apply/', status.HTTP_400_BAD_REQUEST)
    )
    @ddt.unpack
    def test_submit_financial_assistance_request_v2(self, referrer_url, expected_status, *args):
        form_data = {
            'username': self.user.username,
            'course': 'course-v1:test+TestX+Test_Course',
            'income': '$25,000 - $40,000',
            'reason_for_applying': "It's just basic chemistry, yo.",
            'goals': "I don't know if it even matters, but... work with my hands, I guess.",
            'effort': "I'm done, okay? You just give me my money, and you and I, we're done.",
            'mktg-permission': False
        }
        response = self._submit_financial_assistance_form(
            form_data,
            submit_url='submit_financial_assistance_request_v2',
            referrer_url=referrer_url
        )
        assert response.status_code == expected_status

    @ddt.data(
        ({}, 400),
        ({'username': 'wwhite'}, 403),
        ({'username': 'dummy', 'course': 'bad course ID'}, 400)
    )
    @ddt.unpack
    def test_submit_financial_assistance_errors(self, data, response_status):
        response = self._submit_financial_assistance_form(data)
        assert response.status_code == response_status

    def test_financial_assistance_login_required(self):
        for url in (
                reverse('financial_assistance'),
                reverse('financial_assistance_form'),
                reverse('submit_financial_assistance_request')
        ):
            self.client.logout()
            response = self.client.get(url)
            self.assertRedirects(response, reverse('signin_user') + '?next=' + url)


# Patching 'lms.djangoapps.courseware.views.views.get_programs' would be ideal,
# but for some unknown reason that patch doesn't seem to be applied.
@patch('openedx.core.djangoapps.catalog.utils.cache')
class TestProgramMarketingView(SharedModuleStoreTestCase):
    """Unit tests for the program marketing page."""
    program_uuid = str(uuid4())
    url = reverse_lazy('program_marketing_view', kwargs={'program_uuid': program_uuid})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        modulestore_course = CourseFactory()
        course_run = CourseRunFactory(key=str(modulestore_course.id))  # lint-amnesty, pylint: disable=no-member
        course = CatalogCourseFactory(course_runs=[course_run])

        cls.data = ProgramFactory(
            courses=[course],
            is_program_eligible_for_one_click_purchase=False,
            uuid=cls.program_uuid,
        )

    def test_404_if_no_data(self, mock_cache):
        """
        Verify that the page 404s if no program data is found.
        """
        mock_cache.get.return_value = None

        response = self.client.get(self.url)
        assert response.status_code == 404

    def test_200(self, mock_cache):
        """
        Verify the view returns a 200.
        """
        mock_cache.get.return_value = self.data

        response = self.client.get(self.url)
        assert response.status_code == 200


# setting TIME_ZONE_DISPLAYED_FOR_DEADLINES explicitly
@override_settings(TIME_ZONE_DISPLAYED_FOR_DEADLINES="UTC")
class BaseDueDateTests(ModuleStoreTestCase):
    """
    Base class that verifies that due dates are rendered correctly on a page
    """
    __test__ = False

    def get_response(self, course):
        """Return the rendered text for the page to be verified"""
        raise NotImplementedError

    def set_up_course(self, **course_kwargs):
        """
        Create a stock course with a specific due date.
        :param course_kwargs: All kwargs are passed to through to the :class:`CourseFactory`
        """
        course = CourseFactory.create(**course_kwargs)
        with self.store.bulk_operations(course.id):
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            section = ItemFactory.create(
                category='sequential',
                parent_location=chapter.location,
                due=datetime(2013, 9, 18, 11, 30, 00),
                format='homework'
            )
            vertical = ItemFactory.create(category='vertical', parent_location=section.location)
            ItemFactory.create(category='problem', parent_location=vertical.location)

        course = modulestore().get_course(course.id)
        assert course.get_children()[0].get_children()[0].due is not None
        CourseEnrollmentFactory(user=self.user, course_id=course.id)
        CourseOverview.load_from_module_store(course.id)
        return course

    def setUp(self):
        super().setUp()
        assert self.client.login(username=self.user.username, password=self.user_password)

        self.time_with_tz = "2013-09-18 11:30:00+00:00"

    def test_backwards_compatibility(self):
        # The test course being used has show_timezone = False in the policy file
        # (and no due_date_display_format set). This is to test our backwards compatibility--
        # in course_module's init method, the date_display_format will be set accordingly to
        # remove the timezone.
        course = self.set_up_course(due_date_display_format=None, show_timezone=False)
        response = self.get_response(course)
        self.assertContains(response, self.time_with_tz)
        # Test that show_timezone has been cleared (which means you get the default value of True).
        assert course.show_timezone

    def test_defaults(self):
        course = self.set_up_course()
        response = self.get_response(course)
        self.assertContains(response, self.time_with_tz)

    def test_format_none(self):
        # Same for setting the due date to None
        course = self.set_up_course(due_date_display_format=None)
        response = self.get_response(course)
        self.assertContains(response, self.time_with_tz)

    def test_format_date(self):
        # due date with no time
        course = self.set_up_course(due_date_display_format="%b %d %y")
        response = self.get_response(course)
        self.assertContains(response, self.time_with_tz)

    def test_format_invalid(self):
        # improperly formatted due_date_display_format falls through to default
        # (value of show_timezone does not matter-- setting to False to make that clear).
        course = self.set_up_course(due_date_display_format="%%%", show_timezone=False)
        response = self.get_response(course)
        self.assertNotContains(response, "%%%")
        self.assertContains(response, self.time_with_tz)


class TestProgressDueDate(BaseDueDateTests):
    """
    Test that the progress page displays due dates correctly
    """
    __test__ = True

    def get_response(self, course):
        """ Returns the HTML for the progress page """
        return self.client.get(reverse('progress', args=[str(course.id)]))


# TODO: LEARNER-71: Delete entire TestAccordionDueDate class
@set_preview_mode(True)
class TestAccordionDueDate(BaseDueDateTests):
    """
    Test that the accordion page displays due dates correctly
    """
    __test__ = True

    def get_response(self, course):
        """ Returns the HTML for the accordion """
        return self.client.get(
            reverse('courseware', args=[str(course.id)]),
            follow=True
        )

    # TODO: LEARNER-71: Delete entire TestAccordionDueDate class
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_backwards_compatibility(self):
        super().test_backwards_compatibility()

    # TODO: LEARNER-71: Delete entire TestAccordionDueDate class
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_defaults(self):
        super().test_defaults()

    # TODO: LEARNER-71: Delete entire TestAccordionDueDate class
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_format_date(self):
        super().test_format_date()

    # TODO: LEARNER-71: Delete entire TestAccordionDueDate class
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_format_invalid(self):
        super().test_format_invalid()

    # TODO: LEARNER-71: Delete entire TestAccordionDueDate class
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_format_none(self):
        super().test_format_none()


class StartDateTests(ModuleStoreTestCase):
    """
    Test that start dates are properly localized and displayed on the student
    dashboard.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

    def set_up_course(self):
        """
        Create a stock course with a specific due date.
        :param course_kwargs: All kwargs are passed to through to the :class:`CourseFactory`
        """
        course = CourseFactory.create(start=datetime(2013, 9, 16, 7, 17, 28))
        course = modulestore().get_course(course.id)
        return course

    def get_about_response(self, course_key):
        """
        Get the text of the /about page for the course.
        """
        return self.client.get(reverse('about_course', args=[str(course_key)]))

    @patch('common.djangoapps.util.date_utils.pgettext', fake_pgettext(translations={
        ("abbreviated month name", "Sep"): "SEPTEMBER",
    }))
    @patch('common.djangoapps.util.date_utils.gettext', fake_ugettext(translations={
        "SHORT_DATE_FORMAT": "%Y-%b-%d",
    }))
    def test_format_localized_in_studio_course(self):
        course = self.set_up_course()
        response = self.get_about_response(course.id)
        # The start date is set in the set_up_course function above.
        # This should return in the format '%Y-%m-%dT%H:%M:%S%z'
        self.assertContains(response, "2013-09-16T07:17:28+0000")


class ProgressPageBaseTests(ModuleStoreTestCase):
    """
    Base class for progress page tests.
    """

    ENABLED_CACHES = ['default', 'mongo_modulestore_inheritance', 'loc_cache']
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        assert self.client.login(username=self.user.username, password='test')

        self.setup_course()

    def create_course(self, **options):
        """Create the test course."""
        self.course = CourseFactory.create(  # pylint: disable=attribute-defined-outside-init
            start=datetime(2013, 9, 16, 7, 17, 28),
            end=datetime.now(),
            certificate_available_date=datetime.now(UTC),
            certificates_display_behavior=CertificatesDisplayBehaviors.END_WITH_DATE,
            **options,
        )

    def setup_course(self, **course_options):
        """Create the test course and content, and enroll the user."""
        self.create_course(**course_options, grading_policy={'GRADE_CUTOFFS': {'çü†øƒƒ': 0.75, 'Pass': 0.5}})
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(category='chapter', parent_location=self.course.location)
            self.section = ItemFactory.create(category='sequential', parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category='vertical', parent_location=self.section.location)

        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.HONOR)

    def _get_progress_page(self, expected_status_code=200):
        """
        Gets the progress page for the currently logged-in user.
        """
        resp = self.client.get(
            reverse('progress', args=[str(self.course.id)])
        )
        assert resp.status_code == expected_status_code
        return resp

    def _get_student_progress_page(self, expected_status_code=200):
        """
        Gets the progress page for the user in the course.
        """
        resp = self.client.get(
            reverse('student_progress', args=[str(self.course.id), self.user.id])
        )
        assert resp.status_code == expected_status_code
        return resp


# pylint: disable=protected-access
@patch('lms.djangoapps.certificates.api.get_active_web_certificate', PropertyMock(return_value=True))
@ddt.ddt
class ProgressPageTests(ProgressPageBaseTests):
    """
    Tests that verify that the progress page works correctly.
    """
    @ddt.data('"><script>alert(1)</script>', '<script>alert(1)</script>', '</script><script>alert(1)</script>')
    def test_progress_page_xss_prevent(self, malicious_code):
        """
        Test that XSS attack is prevented
        """
        resp = self._get_student_progress_page()
        # Test that malicious code does not appear in html
        self.assertNotContains(resp, malicious_code)

    def test_pure_ungraded_xblock(self):
        ItemFactory.create(category='acid', parent_location=self.vertical.location)
        self._get_progress_page()

    def test_student_progress_with_valid_and_invalid_id(self):
        """
         Check that invalid 'student_id' raises Http404.
        """

        # Create new course
        # Enroll student into course
        self.course = CourseFactory.create()  # lint-amnesty, pylint: disable=attribute-defined-outside-init
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.HONOR)

        # Invalid Student Ids (Integer and Non-int)
        invalid_student_ids = [
            991021,
            'azU3N_8$',
        ]
        for invalid_id in invalid_student_ids:

            resp = self.client.get(
                reverse('student_progress', args=[str(self.course.id), invalid_id])
            )
            assert resp.status_code == 404

        # Assert that valid 'student_id' returns 200 status
        self._get_student_progress_page()

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_unenrolled_student_progress_for_credit_course(self, default_store):
        """
         Test that student progress page does not break while checking for an unenrolled student.
         Scenario: When instructor checks the progress of a student who is not enrolled in credit course.
         It should return 200 response.
        """
        # Create a new course, a user which will not be enrolled in course, admin user for staff access
        course = CourseFactory.create(default_store=default_store)
        admin = AdminFactory.create()
        assert self.client.login(username=admin.username, password='test')

        # Create and enable Credit course
        CreditCourse.objects.create(course_key=course.id, enabled=True)

        # Configure a credit provider for the course
        CreditProvider.objects.create(
            provider_id="ASU",
            enable_integration=True,
            provider_url="https://credit.example.com/request"
        )

        requirements = [{
            "namespace": "grade",
            "name": "grade",
            "display_name": "Grade",
            "criteria": {"min_grade": 0.52},
        }]
        # Add a single credit requirement (final grade)
        set_credit_requirements(course.id, requirements)

        self._get_student_progress_page()

    def test_non_ascii_grade_cutoffs(self):
        self._get_progress_page()

    def test_generate_cert_config(self):

        resp = self._get_progress_page()
        self.assertNotContains(resp, 'Request Certificate')

        # Enable the feature, but do not enable it for this course
        CertificateGenerationConfiguration(enabled=True).save()

        resp = self._get_progress_page()
        self.assertNotContains(resp, 'Request Certificate')

        # Enable certificate generation for this course
        certs_api.set_cert_generation_enabled(self.course.id, True)

        resp = self._get_progress_page()
        self.assertNotContains(resp, 'Request Certificate')

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_view_certificate_for_unverified_student(self):
        """
        If user has already generated a certificate, it should be visible in case of user being
        unverified too.
        """
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        # Enable the feature, but do not enable it for this course
        CertificateGenerationConfiguration(enabled=True).save()

        # Enable certificate generation for this course
        certs_api.set_cert_generation_enabled(self.course.id, True)
        CourseEnrollment.enroll(self.user, self.course.id, mode="verified")

        # Check that the user is unverified
        assert not IDVerificationService.user_is_verified(self.user)
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = True
            course_grade.summary = {'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [],
                                    'grade_breakdown': {}}
            resp = self._get_progress_page()
            self.assertNotContains(resp, "Certificate unavailable")
            self.assertContains(resp, "Your certificate is available")

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_view_certificate_link(self):
        """
        If certificate web view is enabled then certificate web view button should appear for user who certificate is
        available/generated
        """
        certificate = GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='honor'
        )

        # Enable the feature, but do not enable it for this course
        CertificateGenerationConfiguration(enabled=True).save()

        # Enable certificate generation for this course
        certs_api.set_cert_generation_enabled(self.course.id, True)

        # Course certificate configurations
        certificates = [
            {
                'id': 1,
                'name': 'Name 1',
                'description': 'Description 1',
                'course_title': 'course_title_1',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]

        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.update_course(self.course, self.user.id)

        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = True
            course_grade.summary = {'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': {}}

            resp = self._get_progress_page()

            self.assertContains(resp, "View Certificate")

            self.assertContains(resp, "earned a certificate for this course")
            cert_url = certs_api.get_certificate_url(course_id=self.course.id, uuid=certificate.verify_uuid)
            self.assertContains(resp, cert_url)

            # when course certificate is not active
            certificates[0]['is_active'] = False
            self.update_course(self.course, self.user.id)

            resp = self._get_progress_page()
            self.assertNotContains(resp, "View my Certificate")
            self.assertNotContains(resp, "You can now View my Certificate")
            self.assertContains(resp, "Your certificate is available")
            self.assertContains(resp, "earned a certificate for this course.")

    @ddt.data(
        (True, 52),
        (False, 52),
    )
    @ddt.unpack
    def test_progress_queries_paced_courses(self, self_paced, query_count):
        """Test that query counts remain the same for self-paced and instructor-paced courses."""
        # TODO: decrease query count as part of REVO-28
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        self.setup_course(self_paced=self_paced)
        with self.assertNumQueries(query_count, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST), check_mongo_calls(2):
            self._get_progress_page()

    def test_progress_queries(self):
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        self.setup_course()
        with self.assertNumQueries(
            52, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST
        ), check_mongo_calls(2):
            self._get_progress_page()

        for _ in range(2):
            with self.assertNumQueries(
                36, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST
            ), check_mongo_calls(2):
                self._get_progress_page()

    @patch.dict(settings.FEATURES, {'ENABLE_CERTIFICATES_IDV_REQUIREMENT': True})
    @ddt.data(
        *itertools.product(
            (
                CourseMode.AUDIT,
                CourseMode.HONOR,
                CourseMode.VERIFIED,
                CourseMode.PROFESSIONAL,
                CourseMode.NO_ID_PROFESSIONAL_MODE,
                CourseMode.CREDIT_MODE
            ),
            (True, False)
        )
    )
    @ddt.unpack
    def test_show_certificate_request_button(self, course_mode, user_verified):
        """Verify that the Request Certificate is not displayed in audit mode."""
        CertificateGenerationConfiguration(enabled=True).save()
        certs_api.set_cert_generation_enabled(self.course.id, True)
        CourseEnrollment.enroll(self.user, self.course.id, mode=course_mode)
        with patch(
            'lms.djangoapps.verify_student.services.IDVerificationService.user_is_verified'
        ) as user_verify:
            user_verify.return_value = user_verified
            with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
                course_grade = mock_create.return_value
                course_grade.passed = True
                course_grade.summary = {
                    'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': {}
                }

                resp = self._get_progress_page()

                cert_button_hidden = course_mode is CourseMode.AUDIT or \
                    course_mode in CourseMode.VERIFIED_MODES and not user_verified

                assert cert_button_hidden == ('Request Certificate' not in resp.content.decode('utf-8'))

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_page_with_invalidated_certificate_with_html_view(self):
        """
        Verify that for html certs if certificate is marked as invalidated than
        re-generate button should not appear on progress page.
        """
        generated_certificate = self.generate_certificate("honor")

        # Course certificate configurations
        certificates = [
            {
                'id': 1,
                'name': 'dummy',
                'description': 'dummy description',
                'course_title': 'dummy title',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]
        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.update_course(self.course, self.user.id)

        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = True
            course_grade.summary = {
                'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': {}
            }

            resp = self._get_progress_page()
            self.assertContains(resp, "View Certificate")
            self.assert_invalidate_certificate(generated_certificate)

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_page_with_allowlisted_certificate_with_html_view(self):
        """
        Verify that view certificate appears for an allowlisted user
        """
        generated_certificate = self.generate_certificate("honor")

        # Course certificate configurations
        certificates = [
            {
                'id': 1,
                'name': 'dummy',
                'description': 'dummy description',
                'course_title': 'dummy title',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]
        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.update_course(self.course, self.user.id)
        CertificateAllowlistFactory.create(
            user=self.user,
            course_id=self.course.id
        )

        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = False
            course_grade.summary = {
                'grade': 'Fail', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': {}
            }

            resp = self._get_progress_page()
            self.assertContains(resp, "View Certificate")
            self.assert_invalidate_certificate(generated_certificate)

    @ddt.data(
        *itertools.product(
            (
                CourseMode.AUDIT,
                CourseMode.HONOR,
                CourseMode.VERIFIED,
                CourseMode.PROFESSIONAL,
                CourseMode.NO_ID_PROFESSIONAL_MODE,
                CourseMode.CREDIT_MODE
            )
        )
    )
    @ddt.unpack
    def test_progress_with_course_duration_limits(self, course_mode):
        """
        Verify that expired banner message appears on progress page, if learner is enrolled
        in audit mode.
        """
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        user = UserFactory.create()
        assert self.client.login(username=user.username, password='test')
        add_course_mode(self.course, mode_slug=CourseMode.AUDIT)
        add_course_mode(self.course)
        CourseEnrollmentFactory(user=user, course_id=self.course.id, mode=course_mode)

        response = self._get_progress_page()
        bannerText = get_expiration_banner_text(user, self.course)

        if course_mode == CourseMode.AUDIT:
            self.assertContains(response, bannerText, html=True)
        else:
            self.assertNotContains(response, bannerText, html=True)

    @ddt.data(
        *itertools.product(
            (
                CourseMode.AUDIT,
                CourseMode.HONOR,
                CourseMode.VERIFIED,
                CourseMode.PROFESSIONAL,
                CourseMode.NO_ID_PROFESSIONAL_MODE,
                CourseMode.CREDIT_MODE
            )
        )
    )
    @ddt.unpack
    def test_progress_without_course_duration_limits(self, course_mode):
        """
        Verify that expired banner message never appears on progress page, regardless
        of course_mode
        """
        CourseDurationLimitConfig.objects.create(enabled=False)
        user = UserFactory.create()
        assert self.client.login(username=user.username, password='test')
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=course_mode
        )
        CourseEnrollmentFactory(user=user, course_id=self.course.id, mode=course_mode)

        response = self._get_progress_page()
        bannerText = get_expiration_banner_text(user, self.course)
        self.assertNotContains(response, bannerText, html=True)

    @patch('lms.djangoapps.courseware.views.views.is_course_passed', PropertyMock(return_value=True))
    @override_settings(FEATURES=FEATURES_WITH_DISABLE_HONOR_CERTIFICATE)
    @ddt.data(CourseMode.AUDIT, CourseMode.HONOR)
    def test_message_for_ineligible_mode(self, course_mode):
        """ Verify that message appears on progress page, if learner is enrolled
         in an ineligible mode.
        """
        user = UserFactory.create()
        assert self.client.login(username=user.username, password='test')
        CourseEnrollmentFactory(user=user, course_id=self.course.id, mode=course_mode)

        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = True
            course_grade.summary = {'grade': 'Pass', 'percent': 0.75, 'section_breakdown': [], 'grade_breakdown': {}}

            response = self._get_progress_page()

            expected_message = ('You are enrolled in the {mode} track for this course. '
                                'The {mode} track does not include a certificate.').format(mode=course_mode)
            self.assertContains(response, expected_message)

    def test_invalidated_cert_data(self):
        """
        Verify that invalidated cert data is returned if cert is invalidated.
        """
        generated_certificate = self.generate_certificate("honor")

        CertificateInvalidationFactory.create(
            generated_certificate=generated_certificate,
            invalidated_by=self.user
        )
        # Invalidate user certificate
        generated_certificate.invalidate()
        response = views.get_cert_data(self.user, self.course, CourseMode.HONOR, MagicMock(passed=True))
        assert response.cert_status == 'invalidated'
        assert response.title == 'Your certificate has been invalidated'

    @override_settings(FEATURES=FEATURES_WITH_DISABLE_HONOR_CERTIFICATE)
    def test_downloadable_get_cert_data(self):
        """
        Verify that downloadable cert data is returned if cert is downloadable even
        when DISABLE_HONOR_CERTIFICATES feature flag is turned ON.
        """
        self.generate_certificate("honor")
        response = views.get_cert_data(
            self.user, self.course, CourseMode.HONOR, MagicMock(passed=True)
        )

        assert response.cert_status == 'downloadable'
        assert response.title == 'Your certificate is available'

    def test_generating_get_cert_data(self):
        """
        Verify that generating cert data is returned if cert is generating.
        """
        self.generate_certificate("honor")
        with patch('lms.djangoapps.certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status(is_generating=True)):
            response = views.get_cert_data(self.user, self.course, CourseMode.HONOR, MagicMock(passed=True))

        assert response.cert_status == 'generating'
        assert response.title == "We're working on it..."

    def test_unverified_get_cert_data(self):
        """
        Verify that unverified cert data is returned if cert is unverified.
        """
        self.generate_certificate("honor")
        with patch('lms.djangoapps.certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status(is_unverified=True)):
            response = views.get_cert_data(self.user, self.course, CourseMode.HONOR, MagicMock(passed=True))

        assert response.cert_status == 'unverified'
        assert response.title == 'Certificate unavailable'

    def test_request_get_cert_data(self):
        """
        Verify that requested cert data is returned if cert is to be requested.
        """
        self.generate_certificate("honor")
        with patch('lms.djangoapps.certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status()):
            response = views.get_cert_data(self.user, self.course, CourseMode.HONOR, MagicMock(passed=True))

        assert response.cert_status == 'requesting'
        assert response.title == 'Congratulations, you qualified for a certificate!'

    def test_earned_but_not_available_get_cert_data(self):
        """
        Verify that earned but not available cert data is returned if cert has been earned, but isn't available.
        """
        self.generate_certificate("verified")
        with patch('lms.djangoapps.certificates.api.certificate_downloadable_status',
                   return_value=self.mock_certificate_downloadable_status(earned_but_not_available=True)):
            response = views.get_cert_data(self.user, self.course, CourseMode.VERIFIED, MagicMock(passed=True))

        assert response.cert_status == 'earned_but_not_available'
        assert response.title == 'Your certificate will be available soon!'

    @ddt.data(True, False)
    def test_no_certs_generated_and_not_verified(self, enable_cert_idv_requirement):
        """
        Verify if the learner is not ID Verified, and the certs are not yet generated,
        but the learner is eligible, the get_cert_data would return cert status Unverified
        """
        CertificateGenerationConfiguration(enabled=True).save()
        CertificateGenerationCourseSetting(
            course_key=self.course.id, self_generation_enabled=True
        ).save()
        with patch.dict(settings.FEATURES, ENABLE_CERTIFICATES_IDV_REQUIREMENT=enable_cert_idv_requirement):
            with patch(
                'lms.djangoapps.certificates.api.certificate_downloadable_status',
                return_value=self.mock_certificate_downloadable_status()
            ):
                response = views.get_cert_data(self.user, self.course, CourseMode.VERIFIED, MagicMock(passed=True))

        if not enable_cert_idv_requirement:
            assert response.cert_status == 'requesting'
            assert response.title == 'Congratulations, you qualified for a certificate!'
        else:
            assert response.cert_status == 'unverified'
            assert response.title == 'Certificate unavailable'

    def assert_invalidate_certificate(self, certificate):
        """ Dry method to mark certificate as invalid. And assert the response. """
        CertificateInvalidationFactory.create(
            generated_certificate=certificate,
            invalidated_by=self.user
        )
        # Invalidate user certificate
        certificate.invalidate()
        resp = self._get_progress_page()

        self.assertNotContains(resp, 'Request Certificate')
        self.assertContains(resp, 'Your certificate has been invalidated')
        self.assertContains(resp, 'Please contact your course team if you have any questions.')
        self.assertNotContains(resp, 'View my Certificate')

    def generate_certificate(self, mode):
        """ Dry method to generate certificate. """

        generated_certificate = GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode=mode
        )
        CertificateGenerationConfiguration(enabled=True).save()
        certs_api.set_cert_generation_enabled(self.course.id, True)
        return generated_certificate

    def mock_certificate_downloadable_status(
            self, is_downloadable=False, is_generating=False, is_unverified=False, uuid=None,
            earned_but_not_available=None,
    ):
        """Dry method to mock certificate downloadable status response."""
        return {
            'is_downloadable': is_downloadable,
            'is_generating': is_generating,
            'is_unverified': is_unverified,
            'uuid': uuid,
            'earned_but_not_available': earned_but_not_available,
        }


@ddt.ddt
class ProgressPageShowCorrectnessTests(ProgressPageBaseTests):
    """
    Tests that verify that the progress page works correctly when displaying subsections where correctness is hidden.
    """
    # Constants used in the test data
    NOW = datetime.now(UTC)
    DAY_DELTA = timedelta(days=1)
    YESTERDAY = 'yesterday'
    TODAY = 'today'
    TOMORROW = 'tomorrow'
    GRADER_TYPE = 'Homework'
    DATES = {
        YESTERDAY: NOW - DAY_DELTA,
        TODAY: NOW,
        TOMORROW: NOW + DAY_DELTA,
        None: None,
    }

    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory.create(is_staff=True)

    def setup_course(self, show_correctness='', due_date=None, graded=False, **course_options):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Set up course with a subsection with the given show_correctness, due_date, and graded settings.
        """
        # Use a simple grading policy
        course_options['grading_policy'] = {
            "GRADER": [{
                "type": self.GRADER_TYPE,
                "min_count": 2,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1.0
            }],
            "GRADE_CUTOFFS": {
                'A': .9,
                'B': .33
            }
        }
        self.create_course(**course_options)

        metadata = dict(
            show_correctness=show_correctness,
        )
        if due_date is not None:
            metadata['due'] = due_date
        if graded:
            metadata['graded'] = True
            metadata['format'] = self.GRADER_TYPE

        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(category='chapter', parent_location=self.course.location,
                                              display_name="Section 1")
            self.section = ItemFactory.create(category='sequential', parent_location=self.chapter.location,
                                              display_name="Subsection 1", metadata=metadata)
            self.vertical = ItemFactory.create(category='vertical', parent_location=self.section.location)

        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.HONOR)

    def add_problem(self):
        """
        Add a problem to the subsection
        """
        problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
            question_text='The correct answer is Choice 1',
            choices=[True, False],
            choice_names=['choice_0', 'choice_1']
        )
        self.problem = ItemFactory.create(category='problem', parent_location=self.vertical.location,  # lint-amnesty, pylint: disable=attribute-defined-outside-init
                                          data=problem_xml, display_name='Problem 1')
        # Re-fetch the course from the database
        self.course = self.store.get_course(self.course.id)  # lint-amnesty, pylint: disable=attribute-defined-outside-init

    def answer_problem(self, value=1, max_value=1):
        """
        Submit the given score to the problem on behalf of the user
        """
        # Get the module for the problem, as viewed by the user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            self.course,
            depth=2
        )
        self.addCleanup(set_current_request, None)
        module = get_module(
            self.user,
            get_mock_request(self.user),
            self.problem.scope_ids.usage_id,
            field_data_cache,
        )

        # Submit the given score/max_score to the problem xmodule
        grade_dict = {'value': value, 'max_value': max_value, 'user_id': self.user.id}
        module.system.publish(self.problem, 'grade', grade_dict)

    def assert_progress_page_show_grades(self, response, show_correctness, due_date, graded,
                                         show_grades, score, max_score, avg):  # lint-amnesty, pylint: disable=unused-argument
        """
        Ensures that grades and scores are shown or not shown on the progress page as required.
        """

        expected_score = f"<dd>{score}/{max_score}</dd>"
        percent = score / float(max_score)

        # Test individual problem scores
        if show_grades:
            # If grades are shown, we should be able to see the current problem scores.
            self.assertContains(response, expected_score)

            if graded:
                expected_summary_text = "Problem Scores:"
            else:
                expected_summary_text = "Practice Scores:"

        else:
            # If grades are hidden, we should not be able to see the current problem scores.
            self.assertNotContains(response, expected_score)

            if graded:
                expected_summary_text = "Problem scores are hidden"
            else:
                expected_summary_text = "Practice scores are hidden"

            if show_correctness == ShowCorrectness.PAST_DUE and due_date:
                expected_summary_text += ' until the due date.'
            else:
                expected_summary_text += '.'

        # Ensure that expected text is present
        self.assertContains(response, expected_summary_text)

        # Test overall sequential score
        if graded and max_score > 0:
            percentageString = f"{percent:.0%}" if max_score > 0 else ""
            template = '<span> ({0:.3n}/{1:.3n}) {2}</span>'
            expected_grade_summary = template.format(float(score),
                                                     float(max_score),
                                                     percentageString)

            if show_grades:
                self.assertContains(response, expected_grade_summary)
            else:
                self.assertNotContains(response, expected_grade_summary)

    @ddt.data(
        ('', None, False),
        ('', None, True),
        (ShowCorrectness.ALWAYS, None, False),
        (ShowCorrectness.ALWAYS, None, True),
        (ShowCorrectness.ALWAYS, YESTERDAY, False),
        (ShowCorrectness.ALWAYS, YESTERDAY, True),
        (ShowCorrectness.ALWAYS, TODAY, False),
        (ShowCorrectness.ALWAYS, TODAY, True),
        (ShowCorrectness.ALWAYS, TOMORROW, False),
        (ShowCorrectness.ALWAYS, TOMORROW, True),
        (ShowCorrectness.NEVER, None, False),
        (ShowCorrectness.NEVER, None, True),
        (ShowCorrectness.NEVER, YESTERDAY, False),
        (ShowCorrectness.NEVER, YESTERDAY, True),
        (ShowCorrectness.NEVER, TODAY, False),
        (ShowCorrectness.NEVER, TODAY, True),
        (ShowCorrectness.NEVER, TOMORROW, False),
        (ShowCorrectness.NEVER, TOMORROW, True),
        (ShowCorrectness.PAST_DUE, None, False),
        (ShowCorrectness.PAST_DUE, None, True),
        (ShowCorrectness.PAST_DUE, YESTERDAY, False),
        (ShowCorrectness.PAST_DUE, YESTERDAY, True),
        (ShowCorrectness.PAST_DUE, TODAY, False),
        (ShowCorrectness.PAST_DUE, TODAY, True),
        (ShowCorrectness.PAST_DUE, TOMORROW, False),
        (ShowCorrectness.PAST_DUE, TOMORROW, True),
    )
    @ddt.unpack
    def test_progress_page_no_problem_scores(self, show_correctness, due_date_name, graded):
        """
        Test that "no problem scores are present" for a course with no problems,
        regardless of the various show correctness settings.
        """
        self.setup_course(show_correctness=show_correctness, due_date=self.DATES[due_date_name], graded=graded)
        resp = self._get_progress_page()

        # Test that no problem scores are present
        self.assertContains(resp, 'No problem scores in this section')

    @ddt.data(
        ('', None, False, True),
        ('', None, True, True),
        (ShowCorrectness.ALWAYS, None, False, True),
        (ShowCorrectness.ALWAYS, None, True, True),
        (ShowCorrectness.ALWAYS, YESTERDAY, False, True),
        (ShowCorrectness.ALWAYS, YESTERDAY, True, True),
        (ShowCorrectness.ALWAYS, TODAY, False, True),
        (ShowCorrectness.ALWAYS, TODAY, True, True),
        (ShowCorrectness.ALWAYS, TOMORROW, False, True),
        (ShowCorrectness.ALWAYS, TOMORROW, True, True),
        (ShowCorrectness.NEVER, None, False, False),
        (ShowCorrectness.NEVER, None, True, False),
        (ShowCorrectness.NEVER, YESTERDAY, False, False),
        (ShowCorrectness.NEVER, YESTERDAY, True, False),
        (ShowCorrectness.NEVER, TODAY, False, False),
        (ShowCorrectness.NEVER, TODAY, True, False),
        (ShowCorrectness.NEVER, TOMORROW, False, False),
        (ShowCorrectness.NEVER, TOMORROW, True, False),
        (ShowCorrectness.PAST_DUE, None, False, True),
        (ShowCorrectness.PAST_DUE, None, True, True),
        (ShowCorrectness.PAST_DUE, YESTERDAY, False, True),
        (ShowCorrectness.PAST_DUE, YESTERDAY, True, True),
        (ShowCorrectness.PAST_DUE, TODAY, False, True),
        (ShowCorrectness.PAST_DUE, TODAY, True, True),
        (ShowCorrectness.PAST_DUE, TOMORROW, False, False),
        (ShowCorrectness.PAST_DUE, TOMORROW, True, False),
    )
    @ddt.unpack
    def test_progress_page_hide_scores_from_learner(self, show_correctness, due_date_name, graded, show_grades):
        """
        Test that problem scores are hidden on progress page when correctness is not available to the learner, and that
        they are visible when it is.
        """
        due_date = self.DATES[due_date_name]
        self.setup_course(show_correctness=show_correctness, due_date=due_date, graded=graded)
        self.add_problem()

        self.client.login(username=self.user.username, password='test')
        resp = self._get_progress_page()

        # Ensure that expected text is present
        self.assert_progress_page_show_grades(resp, show_correctness, due_date, graded, show_grades, 0, 1, 0)

        # Submit answers to the problem, and re-fetch the progress page
        self.answer_problem()

        resp = self._get_progress_page()

        # Test that the expected text is still present.
        self.assert_progress_page_show_grades(resp, show_correctness, due_date, graded, show_grades, 1, 1, .5)

    @ddt.data(
        ('', None, False, True),
        ('', None, True, True),
        (ShowCorrectness.ALWAYS, None, False, True),
        (ShowCorrectness.ALWAYS, None, True, True),
        (ShowCorrectness.ALWAYS, YESTERDAY, False, True),
        (ShowCorrectness.ALWAYS, YESTERDAY, True, True),
        (ShowCorrectness.ALWAYS, TODAY, False, True),
        (ShowCorrectness.ALWAYS, TODAY, True, True),
        (ShowCorrectness.ALWAYS, TOMORROW, False, True),
        (ShowCorrectness.ALWAYS, TOMORROW, True, True),
        (ShowCorrectness.NEVER, None, False, False),
        (ShowCorrectness.NEVER, None, True, False),
        (ShowCorrectness.NEVER, YESTERDAY, False, False),
        (ShowCorrectness.NEVER, YESTERDAY, True, False),
        (ShowCorrectness.NEVER, TODAY, False, False),
        (ShowCorrectness.NEVER, TODAY, True, False),
        (ShowCorrectness.NEVER, TOMORROW, False, False),
        (ShowCorrectness.NEVER, TOMORROW, True, False),
        (ShowCorrectness.PAST_DUE, None, False, True),
        (ShowCorrectness.PAST_DUE, None, True, True),
        (ShowCorrectness.PAST_DUE, YESTERDAY, False, True),
        (ShowCorrectness.PAST_DUE, YESTERDAY, True, True),
        (ShowCorrectness.PAST_DUE, TODAY, False, True),
        (ShowCorrectness.PAST_DUE, TODAY, True, True),
        (ShowCorrectness.PAST_DUE, TOMORROW, False, True),
        (ShowCorrectness.PAST_DUE, TOMORROW, True, True),
    )
    @ddt.unpack
    def test_progress_page_hide_scores_from_staff(self, show_correctness, due_date_name, graded, show_grades):
        """
        Test that problem scores are hidden from staff viewing a learner's progress page only if show_correctness=never.
        """
        due_date = self.DATES[due_date_name]
        self.setup_course(show_correctness=show_correctness, due_date=due_date, graded=graded)
        self.add_problem()

        # Login as a course staff user to view the student progress page.
        self.client.login(username=self.staff_user.username, password='test')

        resp = self._get_student_progress_page()

        # Ensure that expected text is present
        self.assert_progress_page_show_grades(resp, show_correctness, due_date, graded, show_grades, 0, 1, 0)

        # Submit answers to the problem, and re-fetch the progress page
        self.answer_problem()
        resp = self._get_student_progress_page()

        # Test that the expected text is still present.
        self.assert_progress_page_show_grades(resp, show_correctness, due_date, graded, show_grades, 1, 1, .5)


class VerifyCourseKeyDecoratorTests(TestCase):
    """
    Tests for the ensure_valid_course_key decorator.
    """

    def setUp(self):
        super().setUp()

        self.request = RequestFactoryNoCsrf().get("foo")
        self.valid_course_id = "edX/test/1"
        self.invalid_course_id = "edX/"

    def test_decorator_with_valid_course_id(self):
        mocked_view = create_autospec(views.course_about)
        view_function = ensure_valid_course_key(mocked_view)
        view_function(self.request, course_id=self.valid_course_id)
        assert mocked_view.called

    def test_decorator_with_invalid_course_id(self):
        mocked_view = create_autospec(views.course_about)
        view_function = ensure_valid_course_key(mocked_view)
        self.assertRaises(Http404, view_function, self.request, course_id=self.invalid_course_id)
        assert not mocked_view.called


class GenerateUserCertTests(ModuleStoreTestCase):
    """
    Tests for the view function Generated User Certs
    """

    def setUp(self):
        super().setUp()

        self.student = UserFactory()
        self.course = CourseFactory.create(
            org='edx',
            number='verified',
            end=datetime.now(),
            display_name='Verified Course',
            grading_policy={'GRADE_CUTOFFS': {'cutoff': 0.75, 'Pass': 0.5}},
            self_paced=True,
        )
        self.enrollment = CourseEnrollment.enroll(self.student, self.course.id, mode='honor')
        assert self.client.login(username=self.student, password=TEST_PASSWORD)
        self.url = reverse('generate_user_cert', kwargs={'course_id': str(self.course.id)})

    def test_user_with_out_passing_grades(self):
        # If user has no grading then json will return failed message and badrequest code
        resp = self.client.post(self.url)
        self.assertContains(
            resp,
            "Your certificate will be available when you pass the course.",
            status_code=HttpResponseBadRequest.status_code,
        )

    @patch('lms.djangoapps.courseware.views.views.is_course_passed', return_value=True)
    @override_settings(CERT_QUEUE='certificates')
    def test_user_with_passing_grade(self, mock_is_course_passed):  # lint-amnesty, pylint: disable=unused-argument
        # If user has above passing grading then json will return cert generating message and
        # status valid code
        with patch('xmodule.capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_send_to_queue:
            mock_send_to_queue.return_value = (0, "Successfully queued")

            resp = self.client.post(self.url)
            assert resp.status_code == 200

    def test_user_with_passing_existing_generating_cert(self):
        # If user has passing grade but also has existing generating cert
        # then json will return cert generating message with bad request code
        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = True
            course_grade.summary = {'grade': 'Pass', 'percent': 0.75}

            resp = self.client.post(self.url)
            self.assertContains(resp, "Certificate is being created.", status_code=HttpResponseBadRequest.status_code)

    @override_settings(CERT_QUEUE='certificates')
    def test_user_with_passing_existing_downloadable_cert(self):
        # If user has already downloadable certificate
        # then json will return cert generating message with bad request code

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_create:
            course_grade = mock_create.return_value
            course_grade.passed = True
            course_grade.summay = {'grade': 'Pass', 'percent': 0.75}

            resp = self.client.post(self.url)
            self.assertContains(
                resp,
                "Certificate has already been created.",
                status_code=HttpResponseBadRequest.status_code,
            )

    def test_user_with_non_existing_course(self):
        # If try to access a course with valid key pattern then it will return
        # bad request code with course is not valid message
        resp = self.client.post('/courses/def/abc/in_valid/generate_user_cert')
        self.assertContains(resp, "Course is not valid", status_code=HttpResponseBadRequest.status_code)

    def test_user_with_invalid_course_id(self):
        # If try to access a course with invalid key pattern then 404 will return
        resp = self.client.post('/courses/def/generate_user_cert')
        assert resp.status_code == 404

    def test_user_without_login_return_error(self):
        # If user try to access without login should see a bad request status code with message
        self.client.logout()
        resp = self.client.post(self.url)
        self.assertContains(
            resp,
            "You must be signed in to {platform_name} to create a certificate.".format(
                platform_name=settings.PLATFORM_NAME
            ),
            status_code=HttpResponseBadRequest.status_code,
        )

    def test_certificates_with_passing_grade(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_read_grade:
            course_grade = mock_read_grade.return_value
            course_grade.passed = True

            with patch(
                'lms.djangoapps.certificates.api.generate_certificate_task',
                return_value=None
            ) as mock_cert_task:
                resp = self.client.post(self.url)
                mock_cert_task.assert_called_with(self.student, self.course.id, 'self')
                assert resp.status_code == 200

    def test_certificates_not_passing(self):
        """
        Test course certificates when the user is not passing the course
        """
        with patch(
            'lms.djangoapps.certificates.api.generate_certificate_task',
            return_value=None
        ) as mock_cert_task:
            resp = self.client.post(self.url)
            mock_cert_task.assert_called_with(self.student, self.course.id, 'self')
            self.assertContains(
                resp,
                "Your certificate will be available when you pass the course.",
                status_code=HttpResponseBadRequest.status_code,
            )

    def test_certificates_with_existing_downloadable_cert(self):
        """
        Test course certificates when the user is passing the course and already has a cert
        """
        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_read_grade:
            course_grade = mock_read_grade.return_value
            course_grade.passed = True

            with patch(
                'lms.djangoapps.certificates.api.generate_certificate_task',
                return_value=None
            ) as mock_cert_task:
                resp = self.client.post(self.url)
                mock_cert_task.assert_called_with(self.student, self.course.id, 'self')
                self.assertContains(
                    resp,
                    "Certificate has already been created.",
                    status_code=HttpResponseBadRequest.status_code,
                )


class ActivateIDCheckerBlock(XBlock):
    """
    XBlock for checking for an activate_block_id entry in the render context.
    """
    # We don't need actual children to test this.
    has_children = False

    def student_view(self, context):
        """
        A student view that displays the activate_block_id context variable.
        """
        result = Fragment()
        if 'activate_block_id' in context:
            result.add_content("Activate Block ID: {block_id}</p>".format(block_id=context['activate_block_id']))
        return result


class ViewCheckerBlock(XBlock):
    """
    XBlock for testing user state in views.
    """
    has_children = True
    state = String(scope=Scope.user_state)
    position = 0

    def student_view(self, context):  # pylint: disable=unused-argument
        """
        A student_view that asserts that the ``state`` field for this block
        matches the block's usage_id.
        """
        msg = f"{self.state} != {self.scope_ids.usage_id}"
        assert self.state == str(self.scope_ids.usage_id), msg
        fragments = self.runtime.render_children(self)
        result = Fragment(
            content="<p>ViewCheckerPassed: {}</p>\n{}".format(
                str(self.scope_ids.usage_id),
                "\n".join(fragment.content for fragment in fragments),
            )
        )
        return result


@ddt.ddt
@set_preview_mode(True)
class TestIndexView(ModuleStoreTestCase):
    """
    Tests of the courseware.views.index view.
    """
    @XBlock.register_temp_plugin(ViewCheckerBlock, 'view_checker')
    def test_student_state(self):
        """
        Verify that saved student state is loaded for xblocks rendered in the index view.
        """
        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()
            chapter = ItemFactory.create(parent_location=course.location, category='chapter')
            section = ItemFactory.create(parent_location=chapter.location, category='view_checker',
                                         display_name="Sequence Checker")
            vertical = ItemFactory.create(parent_location=section.location, category='view_checker',
                                          display_name="Vertical Checker")
            block = ItemFactory.create(parent_location=vertical.location, category='view_checker',
                                       display_name="Block Checker")

        for item in (section, vertical, block):
            StudentModuleFactory.create(
                student=self.user,
                course_id=course.id,
                module_state_key=item.scope_ids.usage_id,
                state=json.dumps({'state': str(item.scope_ids.usage_id)})
            )

        CourseOverview.load_from_module_store(course.id)
        CourseEnrollmentFactory(user=self.user, course_id=course.id)

        assert self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.get(
            reverse(
                'courseware_section',
                kwargs={
                    'course_id': str(course.id),
                    'chapter': chapter.url_name,
                    'section': section.url_name,
                }
            )
        )
        # Trigger the assertions embedded in the ViewCheckerBlocks
        self.assertContains(response, "ViewCheckerPassed", count=3)

    @XBlock.register_temp_plugin(ActivateIDCheckerBlock, 'id_checker')
    def test_activate_block_id(self):
        course = CourseFactory.create()
        with self.store.bulk_operations(course.id):
            chapter = ItemFactory.create(parent=course, category='chapter')
            section = ItemFactory.create(parent=chapter, category='sequential', display_name="Sequence")
            vertical = ItemFactory.create(parent=section, category='vertical', display_name="Vertical")
            ItemFactory.create(parent=vertical, category='id_checker', display_name="ID Checker")

        CourseOverview.load_from_module_store(course.id)
        CourseEnrollmentFactory(user=self.user, course_id=course.id)

        assert self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.get(
            reverse(
                'courseware_section',
                kwargs={
                    'course_id': str(course.id),
                    'chapter': chapter.url_name,
                    'section': section.url_name,
                }
            ) + '?activate_block_id=test_block_id'
        )
        self.assertContains(response, "Activate Block ID: test_block_id")

    @patch('lms.djangoapps.courseware.views.views.CourseTabView.course_open_for_learner_enrollment')
    @patch('openedx.core.djangoapps.util.user_messages.PageLevelMessages.register_warning_message')
    def test_courseware_messages_differentiate_for_anonymous_users(
            self, patch_register_warning_message, patch_course_open_for_learner_enrollment
    ):
        """
        Tests that the anonymous user case for the
        register_user_access_warning_messages returns different
        messaging based on the possibility of enrollment
        """
        course = CourseFactory()

        user = self.create_user_for_course(course, CourseUserType.ANONYMOUS)
        request = RequestFactory().get('/')
        request.user = user

        patch_course_open_for_learner_enrollment.return_value = False
        views.CourseTabView.register_user_access_warning_messages(request, course)
        open_for_enrollment_message = patch_register_warning_message.mock_calls[0][1][1]

        patch_register_warning_message.reset_mock()

        patch_course_open_for_learner_enrollment.return_value = True
        views.CourseTabView.register_user_access_warning_messages(request, course)
        closed_to_enrollment_message = patch_register_warning_message.mock_calls[0][1][1]

        assert open_for_enrollment_message != closed_to_enrollment_message

    @patch('openedx.core.djangoapps.util.user_messages.PageLevelMessages.register_warning_message')
    def test_courseware_messages_masters_only(self, patch_register_warning_message):
        with patch(
                'lms.djangoapps.courseware.views.views.CourseTabView.course_open_for_learner_enrollment'
        ) as patch_course_open_for_learner_enrollment:
            course = CourseFactory()

            user = self.create_user_for_course(course, CourseUserType.UNENROLLED)
            request = RequestFactory().get('/')
            request.user = user

            button_html = '<button class="enroll-btn btn-link">Enroll now</button>'

            patch_course_open_for_learner_enrollment.return_value = False
            views.CourseTabView.register_user_access_warning_messages(request, course)
            # pull message out of the calls to the mock so that
            # we can make finer grained assertions than mock provides
            message = patch_register_warning_message.mock_calls[0][1][1]
            assert button_html not in message

            patch_register_warning_message.reset_mock()

            patch_course_open_for_learner_enrollment.return_value = True
            views.CourseTabView.register_user_access_warning_messages(request, course)
            # pull message out of the calls to the mock so that
            # we can make finer grained assertions than mock provides
            message = patch_register_warning_message.mock_calls[0][1][1]
            assert button_html in message

    @ddt.data(
        [True, True, True, False, ],
        [False, True, True, False, ],
        [True, False, True, False, ],
        [True, True, False, False, ],
        [False, False, True, False, ],
        [True, False, False, True, ],
        [False, True, False, False, ],
        [False, False, False, False, ],
    )
    @ddt.unpack
    def test_should_show_enroll_button(self, course_open_for_self_enrollment,
                                       invitation_only, is_masters_only, expected_should_show_enroll_button):
        with patch('lms.djangoapps.courseware.views.views.course_open_for_self_enrollment') \
                as patch_course_open_for_self_enrollment, \
                patch('common.djangoapps.course_modes.models.CourseMode.is_masters_only') \
                as patch_is_masters_only:
            course = CourseFactory()

            patch_course_open_for_self_enrollment.return_value = course_open_for_self_enrollment
            patch_is_masters_only.return_value = is_masters_only
            course.invitation_only = invitation_only

            assert views.CourseTabView.course_open_for_learner_enrollment(course) == expected_should_show_enroll_button


@ddt.ddt
@set_preview_mode(True)
class TestIndexViewCompleteOnView(ModuleStoreTestCase, CompletionWaffleTestMixin):
    """
    Tests CompleteOnView is set up correctly in CoursewareIndex.
    """

    def setup_course(self, default_store):
        """
        Set up course content for modulestore.
        """
        # pylint:disable=attribute-defined-outside-init

        self.request_factory = RequestFactoryNoCsrf()

        with modulestore().default_store(default_store):
            self.course = CourseFactory.create()

            with self.store.bulk_operations(self.course.id):

                self.chapter = ItemFactory.create(
                    parent_location=self.course.location, category='chapter', display_name='Week 1'
                )
                self.section_1 = ItemFactory.create(
                    parent_location=self.chapter.location, category='sequential', display_name='Lesson 1'
                )
                self.vertical_1 = ItemFactory.create(
                    parent_location=self.section_1.location, category='vertical', display_name='Subsection 1'
                )
                self.html_1_1 = ItemFactory.create(
                    parent_location=self.vertical_1.location, category='html', display_name="HTML 1_1"
                )
                self.problem_1 = ItemFactory.create(
                    parent_location=self.vertical_1.location, category='problem', display_name="Problem 1"
                )
                self.html_1_2 = ItemFactory.create(
                    parent_location=self.vertical_1.location, category='html', display_name="HTML 1_2"
                )

                self.section_2 = ItemFactory.create(
                    parent_location=self.chapter.location, category='sequential', display_name='Lesson 2'
                )
                self.vertical_2 = ItemFactory.create(
                    parent_location=self.section_2.location, category='vertical', display_name='Subsection 2'
                )
                self.video_2 = ItemFactory.create(
                    parent_location=self.vertical_2.location, category='video', display_name="Video 2"
                )
                self.problem_2 = ItemFactory.create(
                    parent_location=self.vertical_2.location, category='problem', display_name="Problem 2"
                )

        self.section_1_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course.id),
                'chapter': self.chapter.url_name,
                'section': self.section_1.url_name,
            }
        )

        self.section_2_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course.id),
                'chapter': self.chapter.url_name,
                'section': self.section_2.url_name,
            }
        )

        CourseOverview.load_from_module_store(self.course.id)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)
        assert self.client.login(username=self.user.username, password=self.user_password)

    def test_completion_service_disabled(self):

        self.setup_course(ModuleStoreEnum.Type.split)

        response = self.client.get(self.section_1_url)
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')

        response = self.client.get(self.section_2_url)
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')

    def test_completion_service_enabled(self):

        self.override_waffle_switch(True)

        self.setup_course(ModuleStoreEnum.Type.split)

        response = self.client.get(self.section_1_url)
        self.assertContains(response, 'data-mark-completed-on-view-after-delay')
        self.assertContains(response, 'data-mark-completed-on-view-after-delay', count=2)

        request = self.request_factory.post(
            '/',
            data=json.dumps({"completion": 1}),
            content_type='application/json',
        )
        request.user = self.user
        request.session = {}
        response = handle_xblock_callback(
            request,
            str(self.course.id),
            quote_slashes(str(self.html_1_1.scope_ids.usage_id)),
            'publish_completion',
        )
        assert json.loads(response.content.decode('utf-8')) == {'result': 'ok'}

        response = self.client.get(self.section_1_url)
        self.assertContains(response, 'data-mark-completed-on-view-after-delay')
        self.assertContains(response, 'data-mark-completed-on-view-after-delay', count=1)

        request = self.request_factory.post(
            '/',
            data=json.dumps({"completion": 1}),
            content_type='application/json',
        )
        request.user = self.user
        request.session = {}
        response = handle_xblock_callback(
            request,
            str(self.course.id),
            quote_slashes(str(self.html_1_2.scope_ids.usage_id)),
            'publish_completion',
        )
        assert json.loads(response.content.decode('utf-8')) == {'result': 'ok'}

        response = self.client.get(self.section_1_url)
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')

        response = self.client.get(self.section_2_url)
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')


@ddt.ddt
@set_preview_mode(True)
class TestIndexViewWithVerticalPositions(ModuleStoreTestCase):
    """
    Test the index view to handle vertical positions. Confirms that first position is loaded
    if input position is non-positive or greater than number of positions available.
    """

    def setUp(self):
        """
        Set up initial test data
        """
        super().setUp()

        # create course with 3 positions
        self.course = CourseFactory.create()
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(parent_location=self.course.location, category='chapter')
            self.section = ItemFactory.create(parent_location=self.chapter.location, category='sequential',
                                              display_name="Sequence")
            ItemFactory.create(parent_location=self.section.location, category='vertical', display_name="Vertical1")
            ItemFactory.create(parent_location=self.section.location, category='vertical', display_name="Vertical2")
            ItemFactory.create(parent_location=self.section.location, category='vertical', display_name="Vertical3")

        CourseOverview.load_from_module_store(self.course.id)

        self.client.login(username=self.user, password=self.user_password)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)

    def _get_course_vertical_by_position(self, input_position):
        """
        Returns client response to input position.
        """
        return self.client.get(
            reverse(
                'courseware_position',
                kwargs={
                    'course_id': str(self.course.id),
                    'chapter': self.chapter.url_name,
                    'section': self.section.url_name,
                    'position': input_position,
                }
            )
        )

    def _assert_correct_position(self, response, expected_position):
        """
        Asserts that the expected position and the position in the response are the same
        """
        self.assertContains(response, f'data-position="{expected_position}"')

    @ddt.data(("-1", 1), ("0", 1), ("-0", 1), ("2", 2), ("5", 1))
    @ddt.unpack
    def test_vertical_positions(self, input_position, expected_position):
        """
        Tests the following cases:
        * Load first position when negative position inputted.
        * Load first position when 0/-0 position inputted.
        * Load given position when 0 < input_position <= num_positions_available.
        * Load first position when positive position > num_positions_available.
        """
        resp = self._get_course_vertical_by_position(input_position)
        self._assert_correct_position(resp, expected_position)


class TestRenderXBlock(RenderXBlockTestMixin, ModuleStoreTestCase, CompletionWaffleTestMixin):
    """
    Tests for the courseware.render_xblock endpoint.
    This class overrides the get_response method, which is used by
    the tests defined in RenderXBlockTestMixin.
    """
    def setUp(self):
        reload_django_url_config()
        super().setUp()

    def test_render_xblock_with_invalid_usage_key(self):
        """
        Test XBlockRendering with invalid usage key
        """
        response = self.get_response(usage_key='some_invalid_usage_key')
        self.assertContains(response, 'Page not found', status_code=404)

    def get_response(self, usage_key, url_encoded_params=None):
        """
        Overridable method to get the response from the endpoint that is being tested.
        """
        url = reverse('render_xblock', kwargs={'usage_key_string': str(usage_key)})
        if url_encoded_params:
            url += '?' + url_encoded_params
        return self.client.get(url)

    def test_render_xblock_with_completion_service_disabled(self):
        """
        Test that render_xblock does not set up the CompletionOnViewService.
        """
        self.setup_course(ModuleStoreEnum.Type.split)
        self.setup_user(admin=True, enroll=True, login=True)

        response = self.get_response(usage_key=self.html_block.location)
        assert response.status_code == 200
        self.assertContains(response, 'data-enable-completion-on-view-service="false"')
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')

    def test_render_xblock_with_completion_service_enabled(self):
        """
        Test that render_xblock sets up the CompletionOnViewService for relevant xblocks.
        """
        self.override_waffle_switch(True)

        self.setup_course(ModuleStoreEnum.Type.split)
        self.setup_user(admin=False, enroll=True, login=True)

        response = self.get_response(usage_key=self.html_block.location)
        assert response.status_code == 200
        self.assertContains(response, 'data-enable-completion-on-view-service="true"')
        self.assertContains(response, 'data-mark-completed-on-view-after-delay')

        request = RequestFactoryNoCsrf().post(
            '/',
            data=json.dumps({"completion": 1}),
            content_type='application/json',
        )
        request.user = self.user
        response = handle_xblock_callback(
            request,
            str(self.course.id),
            quote_slashes(str(self.html_block.location)),
            'publish_completion',
        )
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8')) == {'result': 'ok'}

        response = self.get_response(usage_key=self.html_block.location)
        assert response.status_code == 200
        self.assertContains(response, 'data-enable-completion-on-view-service="false"')
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')

        response = self.get_response(usage_key=self.problem_block.location)
        assert response.status_code == 200
        self.assertContains(response, 'data-enable-completion-on-view-service="false"')
        self.assertNotContains(response, 'data-mark-completed-on-view-after-delay')

    def test_rendering_descendant_of_gated_sequence(self):
        """
        Test that we redirect instead of rendering what should be gated content,
        for things that are gated at the sequence level.
        """
        with self.store.default_store(ModuleStoreEnum.Type.split):
            # pylint:disable=attribute-defined-outside-init
            self.course = CourseFactory.create(**self.course_options())
            self.chapter = ItemFactory.create(parent=self.course, category='chapter')
            self.sequence = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name='Sequence',
                is_time_limited=True,
            )
            self.vertical_block = ItemFactory.create(
                parent=self.sequence,
                category='vertical',
                display_name="Vertical",
            )
            self.html_block = ItemFactory.create(
                parent=self.vertical_block,
                category='html',
                data="<p>Test HTML Content<p>"
            )
            self.problem_block = ItemFactory.create(
                parent=self.vertical_block,
                category='problem',
                display_name='Problem'
            )
        CourseOverview.load_from_module_store(self.course.id)
        self.setup_user(admin=False, enroll=True, login=True)

        # Problem and Vertical response should both redirect to the Sequential
        # (where useful messaging would be).
        seq_url = reverse('render_xblock', kwargs={'usage_key_string': str(self.sequence.location)})
        for block in [self.problem_block, self.vertical_block]:
            response = self.get_response(usage_key=block.location)
            assert response.status_code == 302
            assert response.get('Location') == seq_url

        # The Sequence itself 200s (or we risk infinite redirect loops).
        assert self.get_response(usage_key=self.sequence.location).status_code == 200

    def test_rendering_descendant_of_gated_sequence_with_masquerade(self):
        """
        Test that if we are masquerading as a specific student, we do not redirect if content is gated
        """
        with self.store.default_store(ModuleStoreEnum.Type.split):
            # pylint:disable=attribute-defined-outside-init
            self.course = CourseFactory.create(**self.course_options())
            self.chapter = ItemFactory.create(parent=self.course, category='chapter')
            self.sequence = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name='Sequence',
                is_time_limited=True,
            )
            self.vertical_block = ItemFactory.create(
                parent=self.sequence,
                category='vertical',
                display_name="Vertical",
            )
            self.html_block = ItemFactory.create(
                parent=self.vertical_block,
                category='html',
                data="<p>Test HTML Content<p>"
            )
            self.problem_block = ItemFactory.create(
                parent=self.vertical_block,
                category='problem',
                display_name='Problem'
            )
        CourseOverview.load_from_module_store(self.course.id)
        self.setup_user(admin=True, enroll=True, login=True)

        student = UserFactory()
        CourseEnrollment.enroll(student, self.course.id)
        self.update_masquerade(role='student', username=student.username)

        # Problem and Vertical response should both render successfully
        for block in [self.problem_block, self.vertical_block]:
            response = self.get_response(usage_key=block.location)
            assert response.status_code == 200

    def test_render_xblock_with_course_duration_limits(self):
        """
        Verify that expired banner message appears on xblock page, if learner is enrolled
        in audit mode.
        """
        self.setup_course(ModuleStoreEnum.Type.split)
        self.setup_user(admin=False, login=True)

        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        add_course_mode(self.course, mode_slug=CourseMode.AUDIT)
        add_course_mode(self.course)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.AUDIT)

        response = self.get_response(usage_key=self.vertical_block.location)
        assert response.status_code == 200

        banner_text = get_expiration_banner_text(self.user, self.course)
        self.assertContains(response, banner_text, html=True)

    @patch('lms.djangoapps.courseware.views.views.is_request_from_mobile_app')
    def test_render_xblock_with_course_duration_limits_in_mobile_browser(self, mock_is_request_from_mobile_app):
        """
        Verify that expired banner message doesn't appear on xblock page in a mobile browser, if learner is enrolled
        in audit mode.
        """
        mock_is_request_from_mobile_app.return_value = True
        self.setup_course(ModuleStoreEnum.Type.split)
        self.setup_user(admin=False, login=True)

        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        add_course_mode(self.course, mode_slug=CourseMode.AUDIT)
        add_course_mode(self.course)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, mode=CourseMode.AUDIT)

        response = self.get_response(usage_key=self.vertical_block.location)
        assert response.status_code == 200

        banner_text = get_expiration_banner_text(self.user, self.course)
        self.assertNotContains(response, banner_text, html=True)


class TestRenderPublicVideoXBlock(ModuleStoreTestCase):
    """
    Tests for the courseware.render_public_video_xblock endpoint.
    """
    def setup_course(self):
        """
        Helper method to create the course.
        """
        with self.store.default_store(self.store.default_modulestore.get_modulestore_type()):
            course = CourseFactory.create(**{'start': datetime.now() - timedelta(days=1)})
            chapter = ItemFactory.create(parent=course, category='chapter')
            vertical_block = ItemFactory.create(
                parent_location=chapter.location,
                category='vertical',
                display_name="Vertical"
            )
            self.html_block = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=vertical_block,
                category='html',
                data="<p>Test HTML Content<p>"
            )
            self.video_block_public = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=vertical_block,
                category='video',
                display_name='Video with public access',
                metadata={'public_access': True}
            )
            self.video_block_not_public = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
                parent=vertical_block,
                category='video',
                display_name='Video with private access'
            )
        CourseOverview.load_from_module_store(course.id)

    def get_response(self, usage_key):
        """
        Overridable method to get the response from the endpoint that is being tested.
        """
        url = reverse('render_public_video_xblock', kwargs={'usage_key_string': str(usage_key)})
        return self.client.get(url)

    def test_render_xblock_with_invalid_usage_key(self):
        """
        Verify that endpoint returns expected response with invalid usage key
        """
        response = self.get_response(usage_key='some_invalid_usage_key')
        self.assertContains(response, 'Page not found', status_code=404)

    def test_render_xblock_with_non_video_usage_key(self):
        """
        Verify that endpoint returns expected response if usage key block type is not `video`
        """
        self.setup_course()
        response = self.get_response(usage_key=self.html_block.location)
        self.assertContains(response, 'Page not found', status_code=404)

    def test_render_xblock_with_video_usage_key_with_public_access(self):
        """
        Verify that endpoint returns expected response if usage key block type is `video` and video has public access
        """
        self.setup_course()
        response = self.get_response(usage_key=self.video_block_public.location)
        self.assertContains(response, 'Play video', status_code=200)

    def test_render_xblock_with_video_usage_key_with_non_public_access(self):
        """
        Verify that endpoint returns expected response if usage key block type is `video` and video has private access
        """
        self.setup_course()
        response = self.get_response(usage_key=self.video_block_not_public.location)
        self.assertContains(response, 'Page not found', status_code=404)


class TestRenderXBlockSelfPaced(TestRenderXBlock):  # lint-amnesty, pylint: disable=test-inherits-tests
    """
    Test rendering XBlocks for a self-paced course. Relies on the query
    count assertions in the tests defined by RenderXBlockMixin.
    """
    def setUp(self):  # lint-amnesty, pylint: disable=useless-super-delegation
        super().setUp()

    def course_options(self):
        options = super().course_options()
        options['self_paced'] = True
        return options


@set_preview_mode(True)
class TestIndexViewCrawlerStudentStateWrites(SharedModuleStoreTestCase):
    """
    Ensure that courseware index requests do not trigger student state writes.
    This is to prevent locking issues that have caused latency spikes in the
    courseware_studentmodule table when concurrent requests each try to update
    the same rows for sequence, section, and course positions.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the simplest course possible."""
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()
            with cls.store.bulk_operations(cls.course.id):
                cls.chapter = ItemFactory.create(category='chapter', parent_location=cls.course.location)
                cls.section = ItemFactory.create(category='sequential', parent_location=cls.chapter.location)
                cls.vertical = ItemFactory.create(category='vertical', parent_location=cls.section.location)

    @classmethod
    def setUpTestData(cls):  # lint-amnesty, pylint: disable=super-method-not-called
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(is_staff=True)
        CourseEnrollment.enroll(cls.user, cls.course.id)

    def setUp(self):
        """Do the client login."""
        super().setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def test_write_by_default(self):
        """By default, always write student state, regardless of user agent."""
        with patch('lms.djangoapps.courseware.model_data.UserStateCache.set_many') as patched_state_client_set_many:
            # Simulate someone using Chrome
            self._load_courseware('Mozilla/5.0 AppleWebKit/537.36')
            assert patched_state_client_set_many.called
            patched_state_client_set_many.reset_mock()

            # Common crawler user agent
            self._load_courseware('edX-downloader/0.1')
            assert patched_state_client_set_many.called

    def test_writes_with_config(self):
        """Test state writes (or lack thereof) based on config values."""
        CrawlersConfig.objects.create(known_user_agents='edX-downloader,crawler_foo', enabled=True)
        with patch('lms.djangoapps.courseware.model_data.UserStateCache.set_many') as patched_state_client_set_many:
            # Exact matching of crawler user agent
            self._load_courseware('crawler_foo')
            assert not patched_state_client_set_many.called

            # Partial matching of crawler user agent
            self._load_courseware('edX-downloader/0.1')
            assert not patched_state_client_set_many.called

            # Simulate an actual browser hitting it (we should write)
            self._load_courseware('Mozilla/5.0 AppleWebKit/537.36')
            assert patched_state_client_set_many.called

        # Disabling the crawlers config should revert us to default behavior
        CrawlersConfig.objects.create(enabled=False)
        self.test_write_by_default()

    def _load_courseware(self, user_agent):
        """Helper to load the actual courseware page."""
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course.id),
                'chapter': str(self.chapter.location.block_id),
                'section': str(self.section.location.block_id),
            }
        )
        response = self.client.get(url, HTTP_USER_AGENT=user_agent)
        # Make sure we get back an actual 200, and aren't redirected because we
        # messed up the setup somehow (e.g. didn't enroll properly)
        assert response.status_code == 200


class EnterpriseConsentTestCase(EnterpriseTestConsentRequired, ModuleStoreTestCase):
    """
    Ensure that the Enterprise Data Consent redirects are in place only when consent is required.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        assert self.client.login(username=self.user.username, password='test')
        self.course = CourseFactory.create()
        CourseOverview.load_from_module_store(self.course.id)
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)

    @patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    def test_consent_required(self, mock_enterprise_customer_for_request):
        """
        Test that enterprise data sharing consent is required when enabled for the various courseware views.
        """
        # ENT-924: Temporary solution to replace sensitive SSO usernames.
        mock_enterprise_customer_for_request.return_value = None

        course_id = str(self.course.id)
        for url in (
                reverse("courseware", kwargs=dict(course_id=course_id)),
                reverse("progress", kwargs=dict(course_id=course_id)),
                reverse("student_progress", kwargs=dict(course_id=course_id, student_id=str(self.user.id))),
        ):
            self.verify_consent_required(self.client, url)  # lint-amnesty, pylint: disable=no-value-for-parameter


@ddt.ddt
class AccessUtilsTestCase(ModuleStoreTestCase):
    """
    Test access utilities
    """
    @ddt.data(
        (1, False),
        (-1, True)
    )
    @ddt.unpack
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_is_course_open_for_learner(self, start_date_modifier, expected_value):
        staff_user = AdminFactory()
        start_date = datetime.now(UTC) + timedelta(days=start_date_modifier)
        course = CourseFactory.create(start=start_date)

        assert bool(check_course_open_for_learner(staff_user, course)) == expected_value


class DatesTabTestCase(TestCase):
    """
    Ensure that the legacy dates view redirects appropriately (it no longer exists).
    """
    def test_legacy_redirect(self):
        """
        Verify that the legacy dates page redirects to the MFE correctly.
        """
        response = self.client.get('/courses/course-v1:Org+Course+Run/dates?foo=b$r')
        assert response.status_code == 302
        assert response.get('Location') == 'http://learning-mfe/course/course-v1:Org+Course+Run/dates?foo=b%24r'


class MFEUrlTests(TestCase):
    """
    Test url utility method
    """
    @override_settings(LEARNING_MICROFRONTEND_URL='https://learningmfe.openedx.org')
    def test_url_generation(self):
        course_key = CourseKey.from_string("course-v1:OpenEdX+MFE+2020")
        section_key = UsageKey.from_string("block-v1:OpenEdX+MFE+2020+type@sequential+block@Introduction")
        unit_id = "block-v1:OpenEdX+MFE+2020+type@vertical+block@Getting_To_Know_You"
        assert make_learning_mfe_courseware_url(course_key) == (
            'https://learningmfe.openedx.org'
            '/course/course-v1:OpenEdX+MFE+2020'
        )
        assert make_learning_mfe_courseware_url(course_key, params=QueryDict('foo=b$r')) == (
            'https://learningmfe.openedx.org'
            '/course/course-v1:OpenEdX+MFE+2020'
            '?foo=b%24r'
        )
        assert make_learning_mfe_courseware_url(course_key, section_key, '') == (
            'https://learningmfe.openedx.org'
            '/course/course-v1:OpenEdX+MFE+2020'
            '/block-v1:OpenEdX+MFE+2020+type@sequential+block@Introduction'
        )
        assert make_learning_mfe_courseware_url(course_key, section_key, unit_id) == (
            'https://learningmfe.openedx.org'
            '/course/course-v1:OpenEdX+MFE+2020'
            '/block-v1:OpenEdX+MFE+2020+type@sequential+block@Introduction'
            '/block-v1:OpenEdX+MFE+2020+type@vertical+block@Getting_To_Know_You'
        )


class PreviewTests(BaseViewsTestCase):
    """
    Make sure we allow the Legacy view for course previews.
    """
    def test_learner_redirect(self):
        # learners will be redirected by default
        lms_url, mfe_url, __ = self._get_urls()
        assert self.client.get(lms_url).url == mfe_url

    def test_preview_no_redirect(self):
        __, __, preview_url = self._get_urls()
        with set_preview_mode(True):
            # Previews will not redirect to the mfe
            course_staff = UserFactory.create(is_staff=False)
            CourseStaffRole(self.course_key).add_users(course_staff)
            self.client.login(username=course_staff.username, password='test')
            assert self.client.get(preview_url).status_code == 200


class ContentOptimizationTestCase(ModuleStoreTestCase):
    """
    Test our ability to make browser optimizations based on XBlock content.
    """
    def setUp(self):
        super().setUp()
        self.math_html_usage_keys = []

        with self.store.default_store(ModuleStoreEnum.Type.split):
            self.course = CourseFactory.create(display_name='teꜱᴛ course', run="Testing_course")
            with self.store.bulk_operations(self.course.id):
                chapter = ItemFactory.create(
                    category='chapter',
                    parent_location=self.course.location,
                    display_name="Chapter 1",
                )
                section = ItemFactory.create(
                    category='sequential',
                    parent_location=chapter.location,
                    due=datetime(2013, 9, 18, 11, 30, 00),
                    display_name='Sequential 1',
                    format='Homework'
                )
                self.math_vertical = ItemFactory.create(
                    category='vertical',
                    parent_location=section.location,
                    display_name='Vertical with Mathjax HTML',
                )
                self.no_math_vertical = ItemFactory.create(
                    category='vertical',
                    parent_location=section.location,
                    display_name='Vertical with No Mathjax HTML',
                )
                MATHJAX_TAG_PAIRS = [
                    (r"\(", r"\)"),
                    (r"\[", r"\]"),
                    ("[mathjaxinline]", "[/mathjaxinline]"),
                    ("[mathjax]", "[/mathjax]"),
                ]
                for (i, (start_tag, end_tag)) in enumerate(MATHJAX_TAG_PAIRS):
                    math_html_block = ItemFactory.create(
                        category='html',
                        parent_location=self.math_vertical.location,
                        display_name=f"HTML With Mathjax {i}",
                        data=f"<p>Hello Math! {start_tag}x^2 + y^2{end_tag}</p>",
                    )
                    self.math_html_usage_keys.append(math_html_block.location)

                self.html_without_mathjax = ItemFactory.create(
                    category='html',
                    parent_location=self.no_math_vertical.location,
                    display_name="HTML Without Mathjax",
                    data="<p>I talk about mathjax, but I have no actual Math!</p>",
                )

        self.course_key = self.course.id
        self.user = UserFactory(username='staff_user', profile__country='AX', is_staff=True)
        self.date = datetime(2013, 1, 22, tzinfo=UTC)
        self.enrollment = CourseEnrollment.enroll(self.user, self.course_key)
        self.enrollment.created = self.date
        self.enrollment.save()

    @override_waffle_flag(COURSEWARE_OPTIMIZED_RENDER_XBLOCK, True)
    def test_mathjax_detection(self):
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        # Check the HTML blocks with Math
        for usage_key in self.math_html_usage_keys:
            url = reverse("render_xblock", kwargs={'usage_key_string': str(usage_key)})
            response = self.client.get(url)
            assert response.status_code == 200
            assert b"MathJax.Hub.Config" in response.content

        # Check the one without Math...
        url = reverse("render_xblock", kwargs={
            'usage_key_string': str(self.html_without_mathjax.location)
        })
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"MathJax.Hub.Config" not in response.content

        # The containing vertical should still return MathJax (for now)
        url = reverse("render_xblock", kwargs={
            'usage_key_string': str(self.no_math_vertical.location)
        })
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"MathJax.Hub.Config" in response.content

    @override_waffle_flag(COURSEWARE_OPTIMIZED_RENDER_XBLOCK, False)
    def test_mathjax_detection_disabled(self):
        """Check that we can disable optimizations."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        url = reverse("render_xblock", kwargs={
            'usage_key_string': str(self.html_without_mathjax.location)
        })
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"MathJax.Hub.Config" in response.content


@ddt.ddt
class TestCourseWideResources(ModuleStoreTestCase):
    """
    Tests that custom course-wide resources are rendered in course pages
    """

    @ddt.data(
        ('courseware', 'course_id', False, True),
        ('progress', 'course_id', False, False),
        ('instructor_dashboard', 'course_id', True, False),
        ('forum_form_discussion', 'course_id', False, False),
        ('render_xblock', 'usage_key_string', False, True),
    )
    @ddt.unpack
    def test_course_wide_resources(self, url_name, param, is_instructor, is_rendered):
        """
        Tests that the <script> and <link> tags are created for course-wide custom resources.
        Also, test that the order which the resources are added match the given order.
        """
        user = UserFactory()

        js = ['/test.js', 'https://testcdn.com/js/lib.min.js', '//testcdn.com/js/lib2.js']
        css = ['https://testcdn.com/css/lib.min.css', '//testcdn.com/css/lib2.css', '/test.css']

        course = CourseFactory.create(course_wide_js=js, course_wide_css=css)
        chapter = ItemFactory.create(parent_location=course.location, category='chapter')
        sequence = ItemFactory.create(parent_location=chapter.location, category='sequential', display_name='Sequence')

        CourseOverview.load_from_module_store(course.id)
        CourseEnrollmentFactory(user=user, course_id=course.id)
        if is_instructor:
            allow_access(course, user, 'instructor')
        assert self.client.login(username=user.username, password='test')

        kwargs = None
        if param == 'course_id':
            kwargs = {'course_id': str(course.id)}
        elif param == 'usage_key_string':
            kwargs = {'usage_key_string': str(sequence.location)}
        response = self.client.get(reverse(url_name, kwargs=kwargs))

        content = response.content.decode('utf-8')
        js_match = [re.search(f'<script .*src=[\'"]{j}[\'"].*>', content) for j in js]
        css_match = [re.search(f'<link .*href=[\'"]{c}[\'"].*>', content) for c in css]

        # custom resources are included
        if is_rendered:
            assert None not in js_match
            assert None not in css_match

            # custom resources are added in order
            for i in range(len(js) - 1):
                assert js_match[i].start() < js_match[i + 1].start()
            for i in range(len(css) - 1):
                assert css_match[i].start() < css_match[i + 1].start()
        else:
            assert js_match == [None, None, None]
            assert css_match == [None, None, None]
