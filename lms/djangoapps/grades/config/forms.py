"""
Defines a form for providing validation of subsection grade templates.
"""
import logging

from django import forms

from lms.djangoapps.grades.config.models import CoursePersistentGradesFlag

from opaque_keys import InvalidKeyError
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locator import CourseLocator

log = logging.getLogger(__name__)


class CoursePersistentGradesAdminForm(forms.ModelForm):
    """Input form for subsection grade enabling, allowing us to verify data."""

    class Meta(object):
        model = CoursePersistentGradesFlag
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
            msg = u'Course not found. Entered course id was: "{0}". '.format(course_key.to_deprecated_string())
            raise forms.ValidationError(msg)

        return course_key
