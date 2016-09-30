"""
Define steps for bulk email acceptance test.
"""

# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from lettuce.django import mail
from nose.tools import assert_in, assert_equal
from django.core.management import call_command
from django.conf import settings

from courseware.tests.factories import StaffFactory, InstructorFactory


@step(u'Given there is a course with a staff, instructor and student')
def make_populated_course(step):  # pylint: disable=unused-argument
    ## This is different than the function defined in common.py because it enrolls
    ## a staff, instructor, and student member regardless of what `role` is, then
    ## logs `role` in. This is to ensure we have 3 class participants to email.

    # Clear existing courses to avoid conflicts
    world.clear_courses()

    # Create a new course
    course = world.CourseFactory.create(
        org='edx',
        number='888',
        display_name='Bulk Email Test Course'
    )
    world.bulk_email_course_key = course.id

    try:
        # See if we've defined the instructor & staff user yet
        world.bulk_email_instructor
    except AttributeError:
        # Make & register an instructor for the course
        world.bulk_email_instructor = InstructorFactory(course_key=world.bulk_email_course_key)
        world.enroll_user(world.bulk_email_instructor, world.bulk_email_course_key)

        # Make & register a staff member
        world.bulk_email_staff = StaffFactory(course_key=course.id)
        world.enroll_user(world.bulk_email_staff, world.bulk_email_course_key)

    # Make & register a student
    world.register_by_course_key(
        course.id,
        username='student',
        password='test',
        is_staff=False
    )

    # Store the expected recipients
    # given each "send to" option
    staff_emails = [world.bulk_email_staff.email, world.bulk_email_instructor.email]
    world.expected_addresses = {
        'course staff': staff_emails,
        'students, staff, and instructors': staff_emails + ['student@edx.org']
    }


# Dictionary mapping a description of the email recipient
# to the corresponding <option> value in the UI.
SEND_TO_OPTIONS = {
    'myself': 'myself',
    'course staff': 'staff',
    'students, staff, and instructors': 'all'
}


@step(u'I am logged in to the course as "([^"]*)"')
def log_into_the_course(step, role):  # pylint: disable=unused-argument
    # Store the role
    assert_in(role, ['instructor', 'staff'])

    # Log in as the an instructor or staff for the course
    my_email = world.bulk_email_instructor.email
    if role == 'instructor':
        world.log_in(
            username=world.bulk_email_instructor.username,
            password='test',
            email=my_email,
            name=world.bulk_email_instructor.profile.name
        )
    else:
        my_email = world.bulk_email_staff.email
        world.log_in(
            username=world.bulk_email_staff.username,
            password='test',
            email=my_email,
            name=world.bulk_email_staff.profile.name
        )

    # Store the "myself" send to option
    world.expected_addresses['myself'] = [my_email]


@step(u'I send email to "([^"]*)"')
def when_i_send_an_email(step, recipient):  # pylint: disable=unused-argument

    # Check that the recipient is valid
    assert_in(
        recipient, SEND_TO_OPTIONS,
        msg="Invalid recipient: {}".format(recipient)
    )

    # Clear the queue of existing emails
    while not mail.queue.empty():  # pylint: disable=no-member
        mail.queue.get()  # pylint: disable=no-member

    # Because we flush the database before each run,
    # we need to ensure that the email template fixture
    # is re-loaded into the database
    call_command('loaddata', 'course_email_template.json')

    # Go to the email section of the instructor dash
    url = '/courses/{}'.format(world.bulk_email_course_key)
    world.visit(url)
    world.css_click('a[href="{}/instructor"]'.format(url))
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
def then_the_email_is_sent(step, recipient):  # pylint: disable=unused-argument
    # Check that the recipient is valid
    assert_in(
        recipient, SEND_TO_OPTIONS,
        msg="Invalid recipient: {}".format(recipient)
    )

    # Retrieve messages.  Because we are using celery in "always eager"
    # mode, we expect all messages to be sent by this point.
    messages = []
    while not mail.queue.empty():  # pylint: disable=no-member
        messages.append(mail.queue.get())  # pylint: disable=no-member

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
