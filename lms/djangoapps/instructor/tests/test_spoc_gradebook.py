"""
Tests of the instructor dashboard spoc gradebook
"""

from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory, AdminFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware.tests.factories import StudentModuleFactory


USER_COUNT = 11


@attr('shard_1')
class TestGradebook(SharedModuleStoreTestCase):
    """
    Test functionality of the spoc gradebook. Sets up a course with assignments and
    students who've scored various scores on these assignments. Base class for further
    gradebook tests.
    """
    grading_policy = None

    @classmethod
    def setUpClass(cls):
        super(TestGradebook, cls).setUpClass()

        # Create a course with the desired grading policy (from our class attribute)
        kwargs = {}
        if cls.grading_policy is not None:
            kwargs['grading_policy'] = cls.grading_policy
        cls.course = CourseFactory.create(**kwargs)

        # Now give it some content
        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            chapter = ItemFactory.create(
                parent_location=cls.course.location,
                category="sequential",
            )
            section = ItemFactory.create(
                parent_location=chapter.location,
                category="sequential",
                metadata={'graded': True, 'format': 'Homework'}
            )
            cls.items = [
                ItemFactory.create(
                    parent_location=section.location,
                    category="problem",
                    data=StringResponseXMLFactory().build_xml(answer='foo'),
                    metadata={'rerandomize': 'always'}
                )
                for __ in xrange(USER_COUNT - 1)
            ]

    def setUp(self):
        super(TestGradebook, self).setUp()

        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password='test')
        self.users = [UserFactory.create() for _ in xrange(USER_COUNT)]

        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        for i, item in enumerate(self.items):
            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    grade=1 if i < j else 0,
                    max_grade=1,
                    student=user,
                    course_id=self.course.id,
                    module_state_key=item.location
                )

        self.response = self.client.get(reverse(
            'spoc_gradebook',
            args=(self.course.id.to_deprecated_string(),)
        ))

        self.assertEquals(self.response.status_code, 200)


@attr('shard_1')
class TestDefaultGradingPolicy(TestGradebook):
    """
    Tests that the grading policy is properly applied for all users in the course
    Uses the default policy (50% passing rate)
    """
    def test_all_users_listed(self):
        for user in self.users:
            self.assertIn(user.username, unicode(self.response.content, 'utf-8'))

    def test_default_policy(self):
        # Default >= 50% passes, so Users 5-10 should be passing for Homework 1 [6]
        # One use at the top of the page [1]
        self.assertEquals(7, self.response.content.count('grade_Pass'))

        # Users 1-5 attempted Homework 1 (and get Fs) [4]
        # Users 1-10 attempted any homework (and get Fs) [10]
        # Users 4-10 scored enough to not get rounded to 0 for the class (and get Fs) [7]
        # One use at top of the page [1]
        self.assertEquals(22, self.response.content.count('grade_F'))

        # All other grades are None [29 categories * 11 users - 27 non-empty grades = 292]
        # One use at the top of the page [1]
        self.assertEquals(293, self.response.content.count('grade_None'))


@attr('shard_1')
class TestLetterCutoffPolicy(TestGradebook):
    """
    Tests advanced grading policy (with letter grade cutoffs). Includes tests of
    UX display (color, etc).
    """
    grading_policy = {
        "GRADER": [
            {
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1
            },
        ],
        "GRADE_CUTOFFS": {
            'A': .9,
            'B': .8,
            'C': .7,
            'D': .6,
        }
    }

    def test_styles(self):

        self.assertIn("grade_A {color:green;}", self.response.content)
        self.assertIn("grade_B {color:Chocolate;}", self.response.content)
        self.assertIn("grade_C {color:DarkSlateGray;}", self.response.content)
        self.assertIn("grade_D {color:DarkSlateGray;}", self.response.content)

    def test_assigned_grades(self):
        # Users 9-10 have >= 90% on Homeworks [2]
        # Users 9-10 have >= 90% on the class [2]
        # One use at the top of the page [1]
        self.assertEquals(5, self.response.content.count('grade_A'))

        # User 8 has 80 <= Homeworks < 90 [1]
        # User 8 has 80 <= class < 90 [1]
        # One use at the top of the page [1]
        self.assertEquals(3, self.response.content.count('grade_B'))

        # User 7 has 70 <= Homeworks < 80 [1]
        # User 7 has 70 <= class < 80 [1]
        # One use at the top of the page [1]
        self.assertEquals(3, self.response.content.count('grade_C'))

        # User 6 has 60 <= Homeworks < 70 [1]
        # User 6 has 60 <= class < 70 [1]
        # One use at the top of the page [1]
        self.assertEquals(3, self.response.content.count('grade_C'))

        # Users 1-5 have 60% > grades > 0 on Homeworks [5]
        # Users 1-5 have 60% > grades > 0 on the class [5]
        # One use at top of the page [1]
        self.assertEquals(11, self.response.content.count('grade_F'))

        # User 0 has 0 on Homeworks [1]
        # User 0 has 0 on the class [1]
        # One use at the top of the page [1]
        self.assertEquals(3, self.response.content.count('grade_None'))
