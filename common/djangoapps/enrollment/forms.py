from django.core.exceptions import ValidationError
from django.forms import CharField, Form

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from student import forms as student_forms


class CourseEnrollmentsApiListForm(Form):
    """
    A form that validates the query string parameters for the CourseEnrollmentsApiListView.
    """
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
                raise ValidationError("'{}' is not a valid course id.".format(course_id))
        return course_id

    def clean_username(self):
        """
        Validate a string of comma-separated usernames and return a list of usernames.
        """
        usernames_csv_string = self.cleaned_data.get('username')
        if usernames_csv_string:
            usernames = usernames_csv_string.split(',')
            for username in usernames:
                student_forms.validate_username(username)
            return usernames
        return usernames_csv_string
