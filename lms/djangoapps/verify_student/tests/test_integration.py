"""
Integration tests of the payment flow, including course mode selection.
"""

from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.tests.factories import CourseModeFactory


class TestProfEdVerification(ModuleStoreTestCase):
    """
    Integration test for professional ed verification, including course mode selection.
    """

    # Choose an uncommon number for the price so we can search for it on the page
    MIN_PRICE = 1438

    def setUp(self):
        super(TestProfEdVerification, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_key = course.id
        CourseModeFactory(
            mode_slug="professional",
            course_id=self.course_key,
            min_price=self.MIN_PRICE,
            suggested_prices=''
        )

        self.urls = {
            'course_modes_choose': reverse(
                'course_modes_choose',
                args=[unicode(self.course_key)]
            ),

            'verify_student_start_flow': reverse(
                'verify_student_start_flow',
                args=[unicode(self.course_key)]
            ),
        }

    def test_start_flow(self):
        # Go to the course mode page, expecting a redirect to the intro step of the
        # payment flow (since this is a professional ed course). Otherwise, the student
        # would have the option to choose their track.
        resp = self.client.get(self.urls['course_modes_choose'], follow=True)
        self.assertRedirects(resp, self.urls['verify_student_start_flow'])

        # For professional ed courses, expect that the student is NOT enrolled
        # automatically in the course.
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))

        # On the first page of the flow, verify that there's a button allowing the user
        # to proceed to the payment processor; this is the only action the user is allowed to take.
        self.assertContains(resp, 'payment-button')
