"""
Discussion API forms
"""
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, IntegerField

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator


class ThreadListGetForm(Form):
    """
    A form to validate query parameters in the thread list retrieval endpoint
    """
    course_id = CharField()
    page = IntegerField(required=False, min_value=1)
    page_size = IntegerField(required=False, min_value=1)

    def clean_course_id(self):
        """Validate course_id"""
        value = self.cleaned_data["course_id"]
        try:
            return CourseLocator.from_string(value)
        except InvalidKeyError:
            raise ValidationError("'{}' is not a valid course id".format(value))

    def clean_page(self):
        """Return given valid page or default of 1"""
        return self.cleaned_data.get("page") or 1

    def clean_page_size(self):
        """Return given valid page_size (capped at 100) or default of 10"""
        return min(self.cleaned_data.get("page_size") or 10, 100)
