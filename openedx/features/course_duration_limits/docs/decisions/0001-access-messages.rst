1. Pre-formatted Access Messages
================================

Status
------

Accepted

Context
-------

In ``course_duration_limits``, we are adding a new permissions
state that will restrict the user from entering the course.
The point at which this condition is checked is deep within
edx-platform, but the error message needs to display at the
surface of the application. In order to preserve information
display consistency, we want to receive the error message
in the UI in a standard format. We can use ``AccessResponse.user_message``
to store that permission-specific error message. However,
different pages require more or less context. In particular,
when displaying an access error message inside the courseware,
we don't need to specify the current course, but when displaying
the same message on the course dashboard, we do.

Decision
--------

We will add a field to ``AccessResponse``, ``additional_context_user_message``,
which will be used in non-course-specific contexts (for
``course_duration_limits``. The name is non-specific in order to enable it
to be used more generally by other access-control schemes that might have
different levels of context display needs.

Consequences
------------

``AccessResponse`` messages can be more detailed, and more specific
to the required context. The additional attribute on ``AccessResponse``
is somewhat vague, and potentially confusing to a new reader. Which additional
context is relevant is not specified, so if we need more or different
context (rather than just course-context), we will need to rework the
current system or add more attributes.

