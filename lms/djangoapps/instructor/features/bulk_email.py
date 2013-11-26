"""
Define steps for bulk email acceptance test.
"""

#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from lettuce.django import mail
from nose.tools import assert_in, assert_true, assert_equal  # pylint: disable=E0611
from django.core.management import call_command
from django.conf import settings


@step(u'Given I am "([^"]*)" for a course')
def i_am_an_instructor(step, role):  # pylint: disable=W0613

    # Store the role
    assert_in(role, ['instructor', 'staff'])

    # Clear existing courses to avoid conflicts
    world.clear_courses()

    # Create a new course
    course = world.CourseFactory.create(
        org='edx',
        number='999',
        display_name='Test Course'
    )

    # Register the instructor as staff for the course
    world.register_by_course_id(
        'edx/999/Test_Course',
        username='instructor',
        password='password',
        is_staff=True
    )
    world.add_to_course_staff('instructor', '999')

    # Register another staff member
    world.register_by_course_id(
        'edx/999/Test_Course',
        username='staff',
        password='password',
        is_staff=True
    )
    world.add_to_course_staff('staff', '999')

    # Register a student
    world.register_by_course_id(
        'edx/999/Test_Course',
        username='student',
        password='password',
        is_staff=False
    )

    # Log in as the an instructor or staff for the course
    world.log_in(
        username=role,
        password='password',
        email="instructor@edx.org",
        name="Instructor"
    )

    # Store the expected recipients
    # given each "send to" option
    world.expected_addresses = {
        'myself': [role + '@edx.org'],
        'course staff': ['instructor@edx.org', 'staff@edx.org'],
        'students, staff, and instructors': ['instructor@edx.org', 'staff@edx.org', 'student@edx.org']
    }


# Dictionary mapping a description of the email recipient
# to the corresponding <option> value in the UI.
SEND_TO_OPTIONS = {
    'myself': 'myself',
    'course staff': 'staff',
    'students, staff, and instructors': 'all'
}


@step(u'I send email to "([^"]*)"')
def when_i_send_an_email(step, recipient):

    # Check that the recipient is valid
    assert_in(
        recipient, SEND_TO_OPTIONS,
        msg="Invalid recipient: {}".format(recipient)
    )

    # Clear the queue of existing emails
    while not mail.queue.empty():  # pylint: disable=E1101
        mail.queue.get()  # pylint: disable=E1101

    # Because we flush the database before each run,
    # we need to ensure that the email template fixture
    # is re-loaded into the database
    call_command('loaddata', 'course_email_template.json')

    # Go to the email section of the instructor dash
    world.visit('/courses/edx/999/Test_Course')
    world.css_click('a[href="/courses/edx/999/Test_Course/instructor"]')
    world.css_click('div.beta-button-wrapper>a')
    world.css_click('a[data-section="send_email"]')

    # Select the recipient
    world.select_option('send_to', SEND_TO_OPTIONS[recipient])

    # Enter subject and message
    world.css_fill('input#id_subject', 'Hello')

    with world.browser.get_iframe('mce_0_ifr') as iframe:
        editor = iframe.find_by_id('tinymce')[0]
        editor.fill('test message')

    # Click send
    world.css_click('input[name="send"]', dismiss_alert=True)

    # Expect to see a message that the email was sent
    expected_msg = "Your email was successfully queued for sending."
    world.wait_for_visible('#request-response')
    assert_in(
        expected_msg, world.css_text('#request-response'),
        msg="Could not find email success message."
    )


UNSUBSCRIBE_MSG = 'To stop receiving email like this'


@step(u'Email is sent to "([^"]*)"')
def then_the_email_is_sent(step, recipient):

    # Check that the recipient is valid
    assert_in(
        recipient, SEND_TO_OPTIONS,
        msg="Invalid recipient: {}".format(recipient)
    )

    # Retrieve messages.  Because we are using celery in "always eager"
    # mode, we expect all messages to be sent by this point.
    messages = []
    while not mail.queue.empty():  # pylint: disable=E1101
        messages.append(mail.queue.get())  # pylint: disable=E1101

    # Check that we got the right number of messages
    assert_equal(
        len(messages), len(world.expected_addresses[recipient]),
        msg="Received {0} instead of {1} messages for {2}".format(
            len(messages), len(world.expected_addresses[recipient]), recipient
        )
    )

    # Check that the message properties were correct
    recipients = []
    for msg in messages:
        assert_in('Hello', msg.subject)
        assert_in(settings.BULK_EMAIL_DEFAULT_FROM_EMAIL, msg.from_email)

        # Message body should have the message we sent
        # and an unsubscribe message
        assert_in('test message', msg.body)
        assert_in(UNSUBSCRIBE_MSG, msg.body)

        # Should have alternative HTML form
        assert_equal(len(msg.alternatives), 1)
        content, mime_type = msg.alternatives[0]
        assert_equal(mime_type, 'text/html')
        assert_in('test message', content)
        assert_in(UNSUBSCRIBE_MSG, content)

        # Store the recipient address so we can verify later
        recipients.extend(msg.recipients())

    # Check that the messages were sent to the right people
    # Because "myself" can vary based on who sent the message,
    # we use the world.expected_addresses dict we configured
    # in an earlier step.
    for addr in world.expected_addresses[recipient]:
        assert_in(addr, recipients)
