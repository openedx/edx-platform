"""
Tests for the public Python API functions of the Bulk Email app.
"""
from testfixtures import LogCapture

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import InstructorFactory
from lms.djangoapps.bulk_email.api import create_course_email
from lms.djangoapps.bulk_email.data import BulkEmailTargetChoices
from openedx.core.lib.html_to_text import html_to_text


class CreateCourseEmailTests(ModuleStoreTestCase):
    """
    Tests for the `create_course_email` function of the bulk email app's public Python API.
    """
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.target = [BulkEmailTargetChoices.SEND_TO_MYSELF]
        self.subject = "email subject"
        self.html_message = "<p>test message</p>"

    def test_create_course_email(self):
        """
        Happy path test for the `create_course_email` function. Verifies the creation of a CourseEmail instance with
        the bare minimum information required for the function call.
        """
        course_email = create_course_email(
            self.course.id,
            self.instructor,
            self.target,
            self.subject,
            self.html_message,
        )

        assert course_email.sender.id == self.instructor.id
        assert course_email.subject == self.subject
        assert course_email.html_message == self.html_message
        assert course_email.course_id == self.course.id
        assert course_email.text_message == html_to_text(self.html_message)

    def test_create_course_email_with_optional_args(self):
        """
        Additional testing to verify that optional data is used as expected when passed into the `create_course_email`
        function.
        """
        text_message = "everything is awesome!"
        template_name = "gnarly_template"
        from_addr = "blub@noreply.fish.com"

        course_email = create_course_email(
            self.course.id,
            self.instructor,
            self.target,
            self.subject,
            self.html_message,
            text_message=text_message,
            template_name=template_name,
            from_addr=from_addr
        )

        assert course_email.sender.id == self.instructor.id
        assert course_email.subject == self.subject
        assert course_email.html_message == self.html_message
        assert course_email.course_id == self.course.id
        assert course_email.text_message == text_message
        assert course_email.template_name == template_name
        assert course_email.from_addr == from_addr

    def test_create_course_email_expect_exception(self):
        """
        Test to verify behavior when an exception occurs when calling teh `create_course_email` function.
        """
        targets = ["humpty dumpty"]

        expected_messages = [
            f"Cannot create course email for {self.course.id} requested by user {self.instructor} for targets "
            f"{targets}",
        ]

        with self.assertRaises(ValueError):
            with LogCapture() as log:
                create_course_email(
                    self.course.id,
                    self.instructor,
                    targets,
                    self.subject,
                    self.html_message
                )

        for index, message in enumerate(expected_messages):
            assert message in log.records[index].getMessage()
