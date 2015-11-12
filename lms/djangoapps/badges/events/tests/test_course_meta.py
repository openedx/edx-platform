"""
Tests the course meta badging events
"""

from django.test.utils import override_settings
from mock import patch

from django.conf import settings

from badges.backends.base import BadgeBackend
from badges.tests.factories import RandomBadgeClassFactory, CourseEventBadgesConfigurationFactory, BadgeAssertionFactory
from certificates.models import GeneratedCertificate, CertificateStatuses
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class DummyBackend(BadgeBackend):
    """
    Dummy backend that creates assertions without contacting any real-world backend.
    """
    def award(self, badge_class, user, evidence_url=None):
        return BadgeAssertionFactory(badge_class=badge_class, user=user)


@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.events.tests.test_course_meta.DummyBackend')
class CourseEnrollmentBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges based on number of courses a user is enrolled in.
    """
    def setUp(self):
        super(CourseEnrollmentBadgeTest, self).setUp()
        self.badge_classes = [
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='edx__course'
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
        # pylint: disable=no-member
        CourseEnrollment.enroll(user, course_key=course.location.course_key)
        self.assertFalse(user.badgeassertion_set.all())

    def test_checkpoint_matches(self):
        """
        Make sure the proper badges are awarded at the right checkpoints.
        """
        user = UserFactory()
        courses = [CourseFactory() for _i in range(3)]
        for course in courses:
            CourseEnrollment.enroll(user, course_key=course.location.course_key)
        # pylint: disable=no-member
        assertions = user.badgeassertion_set.all()
        self.assertEqual(user.badgeassertion_set.all().count(), 1)
        self.assertEqual(assertions[0].badge_class, self.badge_classes[0])

        courses = [CourseFactory() for _i in range(2)]
        for course in courses:
            # pylint: disable=no-member
            CourseEnrollment.enroll(user, course_key=course.location.course_key)
        # pylint: disable=no-member
        assertions = user.badgeassertion_set.all().order_by('id')
        # pylint: disable=no-member
        self.assertEqual(user.badgeassertion_set.all().count(), 2)
        self.assertEqual(assertions[1].badge_class, self.badge_classes[1])

        courses = [CourseFactory() for _i in range(3)]
        for course in courses:
            # pylint: disable=no-member
            CourseEnrollment.enroll(user, course_key=course.location.course_key)
        # pylint: disable=no-member
        assertions = user.badgeassertion_set.all().order_by('id')
        # pylint: disable=no-member
        self.assertEqual(user.badgeassertion_set.all().count(), 3)
        self.assertEqual(assertions[2].badge_class, self.badge_classes[2])


@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.events.tests.test_course_meta.DummyBackend')
class CourseCompletionBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges based on the number of courses completed.
    """
    def setUp(self, **kwargs):
        super(CourseCompletionBadgeTest, self).setUp()
        self.badge_classes = [
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='edx__course'
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
            # pylint: disable=no-member
            user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
        ).save()
        # pylint: disable=no-member
        self.assertFalse(user.badgeassertion_set.all())

    def test_checkpoint_matches(self):
        """
        Make sure the proper badges are awarded at the right checkpoints.
        """
        user = UserFactory()
        courses = [CourseFactory() for _i in range(2)]
        for course in courses:
            GeneratedCertificate(
                # pylint: disable=no-member
                user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
            ).save()
        # pylint: disable=no-member
        assertions = user.badgeassertion_set.all()
        # pylint: disable=no-member
        self.assertEqual(user.badgeassertion_set.all().count(), 1)
        self.assertEqual(assertions[0].badge_class, self.badge_classes[0])

        courses = [CourseFactory() for _i in range(6)]
        for course in courses:
            GeneratedCertificate(
                user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
            ).save()
        # pylint: disable=no-member
        assertions = user.badgeassertion_set.all().order_by('id')
        self.assertEqual(user.badgeassertion_set.all().count(), 2)
        self.assertEqual(assertions[1].badge_class, self.badge_classes[1])

        courses = [CourseFactory() for _i in range(9)]
        for course in courses:
            GeneratedCertificate(
                user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
            ).save()
        # pylint: disable=no-member
        assertions = user.badgeassertion_set.all().order_by('id')
        # pylint: disable=no-member
        self.assertEqual(user.badgeassertion_set.all().count(), 3)
        self.assertEqual(assertions[2].badge_class, self.badge_classes[2])


@patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
@override_settings(BADGING_BACKEND='lms.djangoapps.badges.events.tests.test_course_meta.DummyBackend')
class CourseGroupBadgeTest(ModuleStoreTestCase):
    """
    Tests the event which awards badges when a user completes a set of courses.
    """
    def setUp(self):
        super(CourseGroupBadgeTest, self).setUp()
        self.badge_classes = [
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
            RandomBadgeClassFactory(
                issuing_component='edx__course'
            ),
        ]
        self.courses = []
        for _badge_class in self.badge_classes:
            # pylint: disable=no-member
            self.courses.append([CourseFactory().location.course_key for _i in range(3)])
        lines = [badge_class.slug + ',' + ','.join([unicode(course_key) for course_key in keys])
                 for badge_class, keys in zip(self.badge_classes, self.courses)]
        config = '\r'.join(lines)
        self.config = CourseEventBadgesConfigurationFactory(course_groups=config)
        self.config_map = dict(zip(self.badge_classes, self.courses))

    def test_no_match(self):
        """
        Make sure a badge isn't created before a user's completed any course groups.
        """
        user = UserFactory()
        course = CourseFactory()
        GeneratedCertificate(
            # pylint: disable=no-member
            user=user, course_id=course.location.course_key, status=CertificateStatuses.downloadable
        ).save()
        # pylint: disable=no-member
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
        # pylint: disable=no-member
        classes = [badge.badge_class.id for badge in user.badgeassertion_set.all()]
        source_classes = [badge.id for badge in self.badge_classes]
        self.assertEqual(classes, source_classes)
