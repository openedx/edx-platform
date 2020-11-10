"""
Tests the course meta badging events
"""


import six
from six.moves import range, zip
from ddt import data, ddt, unpack
from django.conf import settings
from django.test.utils import override_settings
from mock import patch

from lms.djangoapps.badges.tests.factories import CourseEventBadgesConfigurationFactory, RandomBadgeClassFactory
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt
@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend')
class CourseEnrollmentBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges based on number of courses a user is enrolled in.
    """

    def setUp(self):
        super(CourseEnrollmentBadgeTest, self).setUp()
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
        self.assertFalse(user.badgeassertion_set.all())

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
        self.assertEqual(user.badgeassertion_set.all().count(), checkpoint)
        self.assertEqual(assertions[checkpoint - 1].badge_class, self.badge_classes[checkpoint - 1])


@ddt
@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend')
class CourseCompletionBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges based on the number of courses completed.
    """

    def setUp(self):
        super(CourseCompletionBadgeTest, self).setUp()
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
        self.assertFalse(user.badgeassertion_set.all())

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
        self.assertEqual(user.badgeassertion_set.all().count(), checkpoint)
        self.assertEqual(assertions[checkpoint - 1].badge_class, self.badge_classes[checkpoint - 1])


@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend')
class CourseGroupBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges when a user completes a set of courses.
    """

    def setUp(self):
        super(CourseGroupBadgeTest, self).setUp()
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
            self.courses.append([CourseFactory().location.course_key for _i in range(3)])
        lines = [badge_class.slug + ',' + ','.join([six.text_type(course_key) for course_key in keys])
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
        self.assertFalse(user.badgeassertion_set.all())

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
                    self.assertTrue(badge_class.get_for_user(user))
                else:
                    self.assertFalse(badge_class.get_for_user(user))
        classes = [badge.badge_class.id for badge in user.badgeassertion_set.all()]
        source_classes = [badge.id for badge in self.badge_classes]
        self.assertEqual(classes, source_classes)
