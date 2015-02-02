"""Define messages for restricted courses.

These messages are displayed to users when they are blocked
from either enrolling in or accessing a course.

"""
from collections import namedtuple


BlockedMessage = namedtuple('BlockedMessage', [
    # A user-facing description of the message
    'description',

    # The mako template used to render the message
    'template',
])


ENROLL_MESSAGES = {
    'default': BlockedMessage(
        description='Default',
        template='static_templates/enrollment_access_block.html'
    ),
    'embargo': BlockedMessage(
        description='Embargo',
        template='static_templates/embargo.html'
    )
}


COURSEWARE_MESSAGES = {
    'default': BlockedMessage(
        description='Default',
        template='static_templates/courseware_access_block.html'
    ),
    'embargo': BlockedMessage(
        description='Embargo',
        template='static_templates/embargo.html'
    )
}
