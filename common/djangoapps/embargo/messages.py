"""Define messages for restricted courses.

These messages are displayed to users when they are blocked
from either enrolling in or accessing a course.

"""
from collections import namedtuple


BlockedMessage = namedtuple('BlockedMessage', [
    # A user-facing description of the message
    'description',
])


ENROLL_MESSAGES = {
    'default': BlockedMessage(
        description='Default',
    ),
}


ACCESS_MESSAGES = {
    'default': BlockedMessage(
        description='Default',
    )
}
