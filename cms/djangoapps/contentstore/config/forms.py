"""
Defines a form for providing validation.
"""
import logging

from django import forms

from contentstore.config.models import CourseNewAssetsPageFlag

from opaque_keys import InvalidKeyError
from six import text_type
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locator import CourseLocator

log = logging.getLogger(__name__)


class CourseNewAssetsPageAdminForm(forms.ModelForm):
    """Input form for new asset page enablement, allowing us to verify user input."""

    class Meta(object):
        model = CourseNewAssetsPageFlag
        fields = '__all__'

    def clean_course_id(self):
        """Validate the course id"""
        cleaned_id = self.cleaned_data["course_id"]
        try:
            course_key = CourseLocator.from_string(cleaned_id)
        except InvalidKeyError:
            msg = u'Course id invalid. Entered course id was: "{0}."'.format(cleaned_id)
            raise forms.ValidationError(msg)

        if not modulestore().has_course(course_key):
            msg = u'Course not found. Entered course id was: "{0}". '.format(text_type(course_key))
            raise forms.ValidationError(msg)

        return course_key
