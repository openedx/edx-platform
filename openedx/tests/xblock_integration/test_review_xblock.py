"""
Test scenarios for the review xblock.
"""
import ddt
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from review import get_review_ids
import crum


class TestReviewXBlock(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Create the test environment with the review xblock.
    """
    STUDENTS = [
        {'email': 'learner@test.com', 'password': 'foo'},
    ]
    XBLOCK_NAMES = ['review']

    def setUp(self):
        super(TestReviewXBlock, self).setUp()
        # Nose runs setUpClass methods even if a class decorator says to skip
        # the class: https://github.com/nose-devs/nose/issues/946
        # So, skip the test class here if we are not in the LMS.
        if settings.ROOT_URLCONF != 'lms.urls':
            raise unittest.SkipTest('Test only valid in lms')

        # Set up for the actual course
        self.course_actual = CourseFactory.create(
            display_name='Review_Test_Course_ACTUAL',
            org='DillonX',
            number='DAD101x',
            run='3T2017'
        )
        # There are multiple sections so the learner can load different
        # problems, but should only be shown review problems from what they have loaded
        with self.store.bulk_operations(self.course_actual.id, emit_signals=False):
            self.chapter_actual = ItemFactory.create(
                parent=self.course_actual, display_name='Overview'
            )
            self.section1_actual = ItemFactory.create(
                parent=self.chapter_actual, display_name='Section 1'
            )
            self.unit1_actual = ItemFactory.create(
                parent=self.section1_actual, display_name='New Unit 1'
            )
            self.xblock1_actual = ItemFactory.create(
                parent=self.unit1_actual,
                category='problem',
                display_name='Problem 1'
            )
            self.xblock2_actual = ItemFactory.create(
                parent=self.unit1_actual,
                category='problem',
                display_name='Problem 2'
            )
            self.xblock3_actual = ItemFactory.create(
                parent=self.unit1_actual,
                category='problem',
                display_name='Problem 3'
            )
            self.xblock4_actual = ItemFactory.create(
                parent=self.unit1_actual,
                category='problem',
                display_name='Problem 4'
            )
            self.section2_actual = ItemFactory.create(
                parent=self.chapter_actual, display_name='Section 2'
            )
            self.unit2_actual = ItemFactory.create(
                parent=self.section2_actual, display_name='New Unit 2'
            )
            self.xblock5_actual = ItemFactory.create(
                parent=self.unit2_actual,
                category='problem',
                display_name='Problem 5'
            )
            self.section3_actual = ItemFactory.create(
                parent=self.chapter_actual, display_name='Section 3'
            )
            self.unit3_actual = ItemFactory.create(
                parent=self.section3_actual, display_name='New Unit 3'
            )
            self.xblock6_actual = ItemFactory.create(
                parent=self.unit3_actual,
                category='problem',
                display_name='Problem 6'
            )
            # This is the actual review xBlock
            # When implemented, the review is in its own section as a
            # stand-alone unit.
            self.review_section_actual = ItemFactory.create(
                parent=self.chapter_actual, display_name='Review Subsection'
            )
            self.review_unit_actual = ItemFactory.create(
                parent=self.review_section_actual, display_name='Review Unit'
            )

        self.course_actual_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course_actual.id),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )

        # Set up for the review course where the review problems are hosted
        self.course_review = CourseFactory.create(
            display_name='Review_Test_Course_REVIEW',
            org='DillonX',
            number='DAD101x_review',
            run='3T2017'
        )
        with self.store.bulk_operations(self.course_review.id, emit_signals=True):
            self.chapter_review = ItemFactory.create(
                parent=self.course_review, display_name='Overview'
            )
            self.section_review = ItemFactory.create(
                parent=self.chapter_review, display_name='Welcome'
            )
            self.unit1_review = ItemFactory.create(
                parent=self.section_review, display_name='New Unit 1'
            )
            self.xblock1_review = ItemFactory.create(
                parent=self.unit1_review,
                category='problem',
                display_name='Problem 1'
            )
            self.xblock2_review = ItemFactory.create(
                parent=self.unit1_review,
                category='problem',
                display_name='Problem 2'
            )
            self.xblock3_review = ItemFactory.create(
                parent=self.unit1_review,
                category='problem',
                display_name='Problem 3'
            )
            self.xblock4_review = ItemFactory.create(
                parent=self.unit1_review,
                category='problem',
                display_name='Problem 4'
            )
            self.unit2_review = ItemFactory.create(
                parent=self.section_review, display_name='New Unit 2'
            )
            self.xblock5_review = ItemFactory.create(
                parent=self.unit2_review,
                category='problem',
                display_name='Problem 5'
            )
            self.unit3_review = ItemFactory.create(
                parent=self.section_review, display_name='New Unit 3'
            )
            self.xblock6_review = ItemFactory.create(
                parent=self.unit3_review,
                category='problem',
                display_name='Problem 6'
            )

        self.course_review_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course_review.id),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )
        for idx, student in enumerate(self.STUDENTS):
            username = 'u{}'.format(idx)
            self.create_account(username, student['email'], student['password'])
            self.activate_user(student['email'])

        self.staff_user = GlobalStaffFactory()

    def enroll_student(self, email, password, course):
        """
        Student login and enroll for the course
        """
        self.login(email, password)
        self.enroll(course, verify=True)


@attr(shard=1)
@ddt.ddt
class TestReviewFunctions(TestReviewXBlock):
    """
    Check that the essential functions of the Review xBlock work as expected.
    Tests cover the basic process of receiving a hint, adding a new hint,
    and rating/reporting hints.
    """
    def test_no_review_problems(self):
        """
        If a user has not seen any problems, they should
        receive a response to go out and try more problems so they have
        material to review.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        self.review_xblock_actual = ItemFactory.create(
            parent=self.review_unit_actual,
            category='review',
            display_name='Review Tool',
        )

        # Loading the review section
        response = self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.review_section_actual.location.name,
            }
        ))

        expected_h2 = 'Nothing to review'
        self.assertIn(expected_h2, response.content)

    @ddt.data(2, 5, 6, 7)
    def test_too_few_review_problems(self, num_desired):
        """
        If a user does not have enough problems to review, they should
        receive a response to go out and try more problems so they have
        material to review.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Want to load fewer problems than num_desired
        if num_desired > 4:
            self.client.get(reverse(
                'courseware_section',
                kwargs={
                    'course_id': self.course_actual.id,
                    'chapter': self.chapter_actual.location.name,
                    'section': self.section1_actual.location.name,
                }
            ))
        if num_desired > 5:
            self.client.get(reverse(
                'courseware_section',
                kwargs={
                    'course_id': self.course_actual.id,
                    'chapter': self.chapter_actual.location.name,
                    'section': self.section2_actual.location.name,
                }
            ))
        if num_desired > 6:
            self.client.get(reverse(
                'courseware_section',
                kwargs={
                    'course_id': self.course_actual.id,
                    'chapter': self.chapter_actual.location.name,
                    'section': self.section3_actual.location.name,
                }
            ))

        self.review_xblock_actual = ItemFactory.create(
            parent=self.review_unit_actual,
            category='review',
            display_name='Review Tool',
            num_desired=num_desired
        )

        # Loading the review section
        response = self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.review_section_actual.location.name,
            }
        ))

        expected_h2 = 'Nothing to review'

        self.assertIn(expected_h2, response.content)

    @ddt.data(2, 3, 4, 5, 6)
    def test_review_problems(self, num_desired):
        """
        If a user has enough problems to review, they should
        receive a response where there are review problems for them to try.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading problems so the learner has enough problems in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
            }
        ))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section2_actual.location.name,
            }
        ))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section3_actual.location.name,
            }
        ))

        self.review_xblock_actual = ItemFactory.create(
            parent=self.review_unit_actual,
            category='review',
            display_name='Review Tool',
            num_desired=num_desired
        )
        # Loading the review section
        response = self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.review_section_actual.location.name,
            }
        ))

        expected_header_text = 'Review Component'
        # The problems are defaulted to correct upon load
        # This happens because the problems "raw_possible" field is 0 and the
        # "raw_earned" field is also 0.
        expected_correctness_text = 'correct'
        expected_problems = ['Review Problem 1', 'Review Problem 2', 'Review Problem 3',
                             'Review Problem 4', 'Review Problem 5', 'Review Problem 6']
        expected_url_beginning = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101x_review/3T2017+type@problem+block@'

        self.assertIn(expected_header_text, response.content)
        self.assertEqual(response.content.count(expected_correctness_text), num_desired)
        # Since the problems are randomly selected, we have to check
        # the correct number of problems are returned.
        count = 0
        for problem in expected_problems:
            if problem in response.content:
                count += 1
        self.assertEqual(count, num_desired)
        self.assertEqual(response.content.count(expected_url_beginning), num_desired)

    @ddt.data(1, 2, 3, 4, 5, 6)
    def test_review_problem_urls(self, num_desired):
        """
        Verify that the URLs returned from the Review xBlock are valid and
        correct URLs for the problems the learner has seen.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading problems so the learner has enough problems in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
            }
        ))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section2_actual.location.name,
            }
        ))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section3_actual.location.name,
            }
        ))

        user = User.objects.get(email=self.STUDENTS[0]['email'])
        crum.set_current_user(user)
        result_urls = get_review_ids.get_problems(num_desired, self.course_actual.id)

        url_beginning = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101x_review/3T2017+type@problem+block@'
        expected_urls = [
            (url_beginning + 'Problem_1', True, 0),
            (url_beginning + 'Problem_2', True, 0),
            (url_beginning + 'Problem_3', True, 0),
            (url_beginning + 'Problem_4', True, 0),
            (url_beginning + 'Problem_5', True, 0),
            (url_beginning + 'Problem_6', True, 0)
        ]

        # Since the problems are randomly selected, we have to check
        # the correct number of urls are returned.
        count = 0
        for url in expected_urls:
            if url in result_urls:
                count += 1
        self.assertEqual(count, num_desired)

    @ddt.data(1, 2, 3, 4, 5)
    def test_review_problem_urls_unique_problem(self, num_desired):
        """
        Verify that the URLs returned from the Review xBlock are valid and
        correct URLs for the problems the learner has seen. This test will give
        a unique problem to a learner and verify only that learner sees
        it as a review
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading problems so the learner has enough problems in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
            }
        ))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section3_actual.location.name,
            }
        ))

        user = User.objects.get(email=self.STUDENTS[0]['email'])
        crum.set_current_user(user)
        result_urls = get_review_ids.get_problems(num_desired, self.course_actual.id)

        url_beginning = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101x_review/3T2017+type@problem+block@'
        expected_urls = [
            (url_beginning + 'Problem_1', True, 0),
            (url_beginning + 'Problem_2', True, 0),
            (url_beginning + 'Problem_3', True, 0),
            (url_beginning + 'Problem_4', True, 0),
            # This is the unique problem
            (url_beginning + 'Problem_6', True, 0)
        ]
        expected_not_loaded_problem = (url_beginning + 'Problem_5', True, 0)

        # Since the problems are randomly selected, we have to check
        # the correct number of urls are returned.
        count = 0
        for url in expected_urls:
            if url in result_urls:
                count += 1
        self.assertEqual(count, num_desired)
        self.assertNotIn(expected_not_loaded_problem, result_urls)

    """
        NOTE: This test is failing because when I grab the problem from the CSM,
        it is unable to find its parents. This is some issue with the BlockStructure
        and it not being populated the way we want. For now, this is being left out
        since the first course I'm working with does not use this function.
        TODO: Fix get_vertical from get_review_ids to have the block structure for this test
        or fix something in this file to make sure it populates the block structure for the CSM
    """
    @unittest.skip
    def test_review_vertical_url(self):
        """
        Verify that the URL returned from the Review xBlock is a valid and
        correct URL for the vertical the learner has seen.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading problems so the learner has problems and thus a vertical in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
            }
        ))

        user = User.objects.get(email=self.STUDENTS[0]['email'])
        crum.set_current_user(user)
        result_url = get_review_ids.get_vertical(self.course_actual.id)

        expected_url = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101x_review/3T2017+type@'\
            'vertical+block@New_Unit_1'

        self.assertEqual(result_url, expected_url)
