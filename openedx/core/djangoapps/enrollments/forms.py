"""
Forms for validating user input to the Course Enrollment related views.
"""


from django.core.exceptions import ValidationError
from django.forms import CharField, Form
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.user_authn.views.registration_form import validate_username


class CourseEnrollmentsApiListForm(Form):
    """
    A form that validates the query string parameters for the CourseEnrollmentsApiListView.
    """
    MAX_USERNAME_COUNT = 100
    username = CharField(required=False)
    course_id = CharField(required=False)

    def clean_course_id(self):
        """
        Validate and return a course ID.
        """
        course_id = self.cleaned_data.get('course_id')
        if course_id:
            try:
                return CourseKey.from_string(course_id)
            except InvalidKeyError:
                raise ValidationError(u"'{}' is not a valid course id.".format(course_id))
        return course_id

    def clean_username(self):
        """
        Validate a string of comma-separated usernames and return a list of usernames.
        """
        usernames_csv_string = self.cleaned_data.get('username')
        if usernames_csv_string:
            usernames = usernames_csv_string.split(',')
            if len(usernames) > self.MAX_USERNAME_COUNT:
                raise ValidationError(
                    u"Too many usernames in a single request - {}. A maximum of {} is allowed".format(
                        len(usernames),
                        self.MAX_USERNAME_COUNT,
                    )
                )
            for username in usernames:
                validate_username(username)
            return usernames
        return usernames_csv_string
