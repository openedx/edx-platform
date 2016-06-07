""" Tests for analytics.distributions """

from django.test import TestCase
from nose.tools import raises
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from instructor_analytics.distributions import profile_distribution, AVAILABLE_PROFILE_FEATURES


class TestAnalyticsDistributions(TestCase):
    '''Test analytics distribution gathering.'''

    def setUp(self):
        super(TestAnalyticsDistributions, self).setUp()
        self.course_id = SlashSeparatedCourseKey('robot', 'course', 'id')

        self.users = [UserFactory(
            profile__gender=['m', 'f', 'o'][i % 3],
            profile__level_of_education=['a', 'hs', 'el'][i % 3],
            profile__year_of_birth=i + 1930
        ) for i in xrange(30)]

        self.ces = [CourseEnrollment.enroll(user, self.course_id)
                    for user in self.users]

    @raises(ValueError)
    def test_profile_distribution_bad_feature(self):
        feature = 'robot-not-a-real-feature'
        self.assertNotIn(feature, AVAILABLE_PROFILE_FEATURES)
        profile_distribution(self.course_id, feature)

    def test_profile_distribution_easy_choice(self):
        feature = 'gender'
        self.assertIn(feature, AVAILABLE_PROFILE_FEATURES)
        distribution = profile_distribution(self.course_id, feature)
        self.assertEqual(distribution.type, 'EASY_CHOICE')
        self.assertEqual(distribution.data['no_data'], 0)
        self.assertEqual(distribution.data['m'], len(self.users) / 3)
        self.assertEqual(distribution.choices_display_names['m'], 'Male')

    def test_profile_distribution_open_choice(self):
        feature = 'year_of_birth'
        self.assertIn(feature, AVAILABLE_PROFILE_FEATURES)
        distribution = profile_distribution(self.course_id, feature)
        print distribution
        self.assertEqual(distribution.type, 'OPEN_CHOICE')
        self.assertTrue(hasattr(distribution, 'choices_display_names'))
        self.assertEqual(distribution.choices_display_names, None)
        self.assertNotIn('no_data', distribution.data)
        self.assertEqual(distribution.data[1930], 1)

    def test_gender_count(self):
        course_enrollments = CourseEnrollment.objects.filter(
            course_id=self.course_id, user__profile__gender='m'
        )
        distribution = profile_distribution(self.course_id, "gender")
        self.assertEqual(distribution.data['m'], len(course_enrollments))
        course_enrollments[0].deactivate()
        distribution = profile_distribution(self.course_id, "gender")
        self.assertEqual(distribution.data['m'], len(course_enrollments) - 1)

    def test_level_of_education_count(self):
        course_enrollments = CourseEnrollment.objects.filter(
            course_id=self.course_id, user__profile__level_of_education='hs'
        )
        distribution = profile_distribution(self.course_id, "level_of_education")
        self.assertEqual(distribution.data['hs'], len(course_enrollments))
        course_enrollments[0].deactivate()
        distribution = profile_distribution(self.course_id, "level_of_education")
        self.assertEqual(distribution.data['hs'], len(course_enrollments) - 1)


class TestAnalyticsDistributionsNoData(TestCase):
    '''Test analytics distribution gathering.'''

    def setUp(self):
        super(TestAnalyticsDistributionsNoData, self).setUp()
        self.course_id = SlashSeparatedCourseKey('robot', 'course', 'id')

        self.users = [UserFactory(
            profile__year_of_birth=i + 1930,
        ) for i in xrange(5)]

        self.nodata_users = [UserFactory(
            profile__year_of_birth=None,
            profile__gender=[None, ''][i % 2]
        ) for i in xrange(4)]

        self.users += self.nodata_users

        self.ces = tuple(CourseEnrollment.enroll(user, self.course_id)
                         for user in self.users)

    def test_profile_distribution_easy_choice_nodata(self):
        feature = 'gender'
        self.assertIn(feature, AVAILABLE_PROFILE_FEATURES)
        distribution = profile_distribution(self.course_id, feature)
        print distribution
        self.assertEqual(distribution.type, 'EASY_CHOICE')
        self.assertTrue(hasattr(distribution, 'choices_display_names'))
        self.assertNotEqual(distribution.choices_display_names, None)
        self.assertIn('no_data', distribution.data)
        self.assertEqual(distribution.data['no_data'], len(self.nodata_users))

    def test_profile_distribution_open_choice_nodata(self):
        feature = 'year_of_birth'
        self.assertIn(feature, AVAILABLE_PROFILE_FEATURES)
        distribution = profile_distribution(self.course_id, feature)
        print distribution
        self.assertEqual(distribution.type, 'OPEN_CHOICE')
        self.assertTrue(hasattr(distribution, 'choices_display_names'))
        self.assertEqual(distribution.choices_display_names, None)
        self.assertIn('no_data', distribution.data)
        self.assertEqual(distribution.data['no_data'], len(self.nodata_users))
