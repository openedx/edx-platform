""" Tests for analytics.distributions """

from django.test import TestCase
from nose.tools import raises
from student.models import CourseEnrollment
from student.tests.factories import UserFactory

from analytics.distributions import profile_distribution, AVAILABLE_PROFILE_FEATURES


class TestAnalyticsDistributions(TestCase):
    '''Test analytics distribution gathering.'''

    def setUp(self):
        self.course_id = 'some/robot/course/id'

        self.users = [UserFactory(
            profile__gender=['m', 'f', 'o'][i % 3],
            profile__year_of_birth=i + 1930
        ) for i in xrange(30)]

        self.ces = [CourseEnrollment.objects.create(
            course_id=self.course_id,
            user=user
        ) for user in self.users]

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


class TestAnalyticsDistributionsNoData(TestCase):
    '''Test analytics distribution gathering.'''

    def setUp(self):
        self.course_id = 'some/robot/course/id'

        self.users = [UserFactory(
            profile__year_of_birth=i + 1930,
        ) for i in xrange(5)]

        self.nodata_users = [UserFactory(
            profile__year_of_birth=None,
            profile__gender=[None, ''][i % 2]
        ) for i in xrange(4)]

        self.users += self.nodata_users

        self.ces = tuple(CourseEnrollment.objects.create(course_id=self.course_id, user=user) for user in self.users)

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
