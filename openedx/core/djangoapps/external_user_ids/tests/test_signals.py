"""
Signal Tests for External User Ids that are sent out of Open edX
"""

from opaque_keys.edx.keys import CourseKey
from django.core.cache import cache
from edx_django_utils.cache import RequestCache

from common.djangoapps.entitlements.models import CourseEntitlement
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    ProgramFactory,
)
from common.djangoapps.student.tests.factories import TEST_PASSWORD, UserFactory, CourseEnrollmentFactory
from openedx.core.djangoapps.catalog.cache import (
    CATALOG_COURSE_PROGRAMS_CACHE_KEY_TPL,
    COURSE_PROGRAMS_CACHE_KEY_TPL,
    PROGRAM_CACHE_KEY_TPL,
)
from openedx.core.djangoapps.external_user_ids.models import ExternalId, ExternalIdType
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.course_modes.models import CourseMode

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class MicrobachelorsExternalIDTest(ModuleStoreTestCase, CacheIsolationTestCase):
    """
    Test cases for Signals for External User Ids
    """
    ENABLED_CACHES = ['default']

    @classmethod
    def setUpClass(cls):
        super(MicrobachelorsExternalIDTest, cls).setUpClass()

        cls.course_list = []
        cls.user = UserFactory.create()
        cls.course_keys = [
            CourseKey.from_string('course-v1:edX+DemoX+Test_Course'),
            CourseKey.from_string('course-v1:edX+DemoX+Another_Test_Course'),
        ]
        ExternalIdType.objects.create(
            name=ExternalIdType.MICROBACHELORS_COACHING,
            description='test'
        )

    def setUp(self):
        super(MicrobachelorsExternalIDTest, self).setUp()
        RequestCache.clear_all_namespaces()
        self.program = self._create_cached_program()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def _create_cached_program(self):
        """ helper method to create a cached program """
        program = ProgramFactory.create()

        for course_key in self.course_keys:
            program['courses'].append(CourseFactory(id=course_key))

        program['type'] = 'MicroBachelors'
        program['type_attrs']['coaching_supported'] = True

        for course in program['courses']:
            cache.set(
                CATALOG_COURSE_PROGRAMS_CACHE_KEY_TPL.format(course_uuid=course['uuid']),
                [program['uuid']],
                None
            )

            course_run = course['course_runs'][0]['key']
            cache.set(
                COURSE_PROGRAMS_CACHE_KEY_TPL.format(course_run_id=course_run),
                [program['uuid']],
                None
            )
        cache.set(
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']),
            program,
            None
        )

        return program

    def test_enroll_mb_create_external_id(self):
        course_run_key = self.program['courses'][0]['course_runs'][0]['key']

        # Enroll user
        enrollment = CourseEnrollmentFactory.create(
            course_id=course_run_key,
            user=self.user,
            mode=CourseMode.VERIFIED,
        )
        enrollment.save()
        external_id = ExternalId.objects.get(
            user=self.user
        )
        assert external_id is not None
        assert external_id.external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING

    def test_second_enroll_mb_no_new_external_id(self):
        course_run_key1 = self.program['courses'][0]['course_runs'][0]['key']
        course_run_key2 = self.program['courses'][1]['course_runs'][0]['key']

        # Enroll user
        CourseEnrollmentFactory.create(
            course_id=course_run_key1,
            user=self.user,
            mode=CourseMode.VERIFIED,
        )
        external_id = ExternalId.objects.get(
            user=self.user
        )
        assert external_id is not None
        assert external_id.external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING
        original_external_user_uuid = external_id.external_user_id

        CourseEnrollmentFactory.create(
            course_id=course_run_key2,
            user=self.user,
            mode=CourseMode.VERIFIED,
        )
        enrollments = CourseEnrollment.objects.filter(user=self.user)

        assert len(enrollments) == 2

        external_ids = ExternalId.objects.filter(
            user=self.user
        )

        assert len(external_ids) == 1
        assert external_ids[0].external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING
        assert original_external_user_uuid == external_ids[0].external_user_id

    def test_entitlement_mb_create_external_id(self):
        catalog_course = self.program['courses'][0]

        assert ExternalId.objects.filter(
            user=self.user
        ).count() == 0

        entitlement = CourseEntitlement.objects.create(
            course_uuid=catalog_course['uuid'],
            mode=CourseMode.VERIFIED,
            user=self.user,
            order_number='TEST-12345'
        )
        entitlement.save()

        external_id = ExternalId.objects.get(
            user=self.user
        )
        assert external_id is not None
        assert external_id.external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING

    def test_second_entitlement_mb_no_new_external_id(self):
        catalog_course1 = self.program['courses'][0]
        catalog_course2 = self.program['courses'][1]

        # Enroll user
        entitlement = CourseEntitlement.objects.create(
            course_uuid=catalog_course1['uuid'],
            mode=CourseMode.VERIFIED,
            user=self.user,
            order_number='TEST-12345'
        )
        entitlement.save()
        external_id = ExternalId.objects.get(
            user=self.user
        )
        assert external_id is not None
        assert external_id.external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING
        original_external_user_uuid = external_id.external_user_id

        CourseEntitlement.objects.create(
            course_uuid=catalog_course2['uuid'],
            mode=CourseMode.VERIFIED,
            user=self.user,
            order_number='TEST-12345'
        )
        entitlements = CourseEntitlement.objects.filter(user=self.user)

        assert len(entitlements) == 2

        external_ids = ExternalId.objects.filter(
            user=self.user
        )

        assert len(external_ids) == 1
        assert external_ids[0].external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING
        assert original_external_user_uuid == external_ids[0].external_user_id
