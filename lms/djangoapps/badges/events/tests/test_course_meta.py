"""
Tests the course meta badging events
"""


from unittest.mock import patch

from ddt import data, ddt, unpack
from django.conf import settings
from django.test.utils import override_settings

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.badges.tests.factories import CourseEventBadgesConfigurationFactory, RandomBadgeClassFactory
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


@ddt
@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend')
class CourseEnrollmentBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges based on number of courses a user is enrolled in.
    """

    def setUp(self):
        super().setUp()
        self.badge_classes = [
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
        ]
        nums = ['3', '5', '8']
        entries = [','.join(pair) for pair in zip(nums, [badge.slug for badge in self.badge_classes])]
        enrollment_config = '\r'.join(entries)
        self.config = CourseEventBadgesConfigurationFactory(courses_enrolled=enrollment_config)

    def test_no_match(self):
        """
        Make sure a badge isn't created before a user's reached any checkpoint.
        """
        user = UserFactory()
        course = CourseFactory()
        CourseEnrollment.enroll(user, course_key=course.location.course_key)
        assert not user.badgeassertion_set.all()

    @unpack
    @data((1, 3), (2, 5), (3, 8))
    def test_checkpoint_matches(self, checkpoint, required_badges):
        """
        Make sure the proper badges are awarded at the right checkpoints.
        """
        user = UserFactory()
        courses = [CourseFactory() for _i in range(required_badges)]
        for course in courses:
            CourseEnrollment.enroll(user, course_key=course.location.course_key)
        assertions = user.badgeassertion_set.all().order_by('id')
        assert user.badgeassertion_set.all().count() == checkpoint
        assert assertions[(checkpoint - 1)].badge_class == self.badge_classes[(checkpoint - 1)]


@ddt
@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend')
class CourseCompletionBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges based on the number of courses completed.
    """

    def setUp(self):
        super().setUp()
        self.badge_classes = [
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
        ]
        nums = ['2', '6', '9']
        entries = [','.join(pair) for pair in zip(nums, [badge.slug for badge in self.badge_classes])]
        completed_config = '\r'.join(entries)
        self.config = CourseEventBadgesConfigurationFactory.create(courses_completed=completed_config)
        self.config.clean_fields()

    def test_no_match(self):
        """
        Make sure a badge isn't created before a user's reached any checkpoint.
        """
        user = UserFactory()
        course = CourseFactory()
        GeneratedCertificate(
            user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
        ).save()
        assert not user.badgeassertion_set.all()

    @unpack
    @data((1, 2), (2, 6), (3, 9))
    def test_checkpoint_matches(self, checkpoint, required_badges):
        """
        Make sure the proper badges are awarded at the right checkpoints.
        """
        user = UserFactory()
        courses = [CourseFactory() for _i in range(required_badges)]
        for course in courses:
            GeneratedCertificate(
                user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
            ).save()
        assertions = user.badgeassertion_set.all().order_by('id')
        assert user.badgeassertion_set.all().count() == checkpoint
        assert assertions[(checkpoint - 1)].badge_class == self.badge_classes[(checkpoint - 1)]


@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend')
class CourseGroupBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges when a user completes a set of courses.
    """

    def setUp(self):
        super().setUp()
        self.badge_classes = [
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='openedx__course'
            ),
        ]
        self.courses = []
        for _badge_class in self.badge_classes:
            self.courses.append([CourseFactory().location.course_key for _i in range(3)])  # lint-amnesty, pylint: disable=no-member
        lines = [badge_class.slug + ',' + ','.join([str(course_key) for course_key in keys])
                 for badge_class, keys in zip(self.badge_classes, self.courses)]
        config = '\r'.join(lines)
        self.config = CourseEventBadgesConfigurationFactory(course_groups=config)
        self.config_map = dict(list(zip(self.badge_classes, self.courses)))

    def test_no_match(self):
        """
        Make sure a badge isn't created before a user's completed any course groups.
        """
        user = UserFactory()
        course = CourseFactory()
        GeneratedCertificate(
            user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
        ).save()
        assert not user.badgeassertion_set.all()

    def test_group_matches(self):
        """
        Make sure the proper badges are awarded when groups are completed.
        """
        user = UserFactory()
        items = list(self.config_map.items())
        for badge_class, course_keys in items:
            for i, key in enumerate(course_keys):
                GeneratedCertificate(
                    user=user, course_id=key, status=CertificateStatuses.downloadable
                ).save()
                # We don't award badges until all three are set.
                if i + 1 == len(course_keys):
                    assert badge_class.get_for_user(user)
                else:
                    assert not badge_class.get_for_user(user)
        classes = [badge.badge_class.id for badge in user.badgeassertion_set.all()]
        source_classes = [badge.id for badge in self.badge_classes]
        assert classes == source_classes
