"""
Define steps for bulk email acceptance test.
"""

from lettuce import world, step
from lettuce.django import mail
from nose.tools import assert_in, assert_true, assert_equal
from django.core.management import call_command


@step(u'I am an instructor for a course')
def i_am_an_instructor(step):

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

    # Log in as the instructor for the course
    world.log_in(
        username='instructor',
        password='password',
        email="instructor@edx.org",
        name="Instructor"
    )


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
    world.css_click('input[name="send"]')

    # Expect to see a message that the email was sent
    # TODO -- identify the message by CSS ID instead of index
    expected_msg = "Your email was successfully queued for sending."
    assert_true(
        world.css_has_text('div.request-response', expected_msg, index=1, allow_blank=False),
        msg="Could not find email success message."
    )


# Dictionaries mapping description of email recipient
# to the expected recipient email addresses
EXPECTED_ADDRESSES = {
    'myself': ['instructor@edx.org'],
    'course staff': ['instructor@edx.org', 'staff@edx.org'],
    'students, staff, and instructors': ['instructor@edx.org', 'staff@edx.org', 'student@edx.org']
}

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
    while not mail.queue.empty():
        messages.append(mail.queue.get())

    # Check that we got the right number of messages
    assert_equal(
        len(messages), len(EXPECTED_ADDRESSES[recipient]),
        msg="Received {0} instead of {1} messages for {2}".format(
            len(messages), len(EXPECTED_ADDRESSES[recipient]), recipient
        )
    )

    # Check that the message properties were correct
    recipients = []
    for msg in messages:
        assert_equal(msg.subject, u'[Test Course] Hello')
        assert_equal(msg.from_email, u'"Test Course" Course Staff <course-updates@edx.org>')

        # Message body should have the message we sent
        # and an unsubscribe message
        assert_in('test message', msg.body)
        assert_in(UNSUBSCRIBE_MSG, msg.body)

        # Should have alternative HTML form
        assert_equal(len(msg.alternatives), 1)
        content, mime_type = msg.alternatives[0]
        assert_in('test message', content)
        assert_in(UNSUBSCRIBE_MSG, content)

        # Store the recipient address so we can verify later
        recipients.extend(msg.recipients())

    # Check that the messages were sent to the right people
    for addr in EXPECTED_ADDRESSES[recipient]:
        assert_in(addr, recipients)
