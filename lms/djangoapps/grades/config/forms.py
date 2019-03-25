"""
Defines a form for providing validation of subsection grade templates.
"""
import logging

from django import forms
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from six import text_type

from lms.djangoapps.grades.config.models import CoursePersistentGradesFlag
from openedx.core.lib.courses import clean_course_id
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class CoursePersistentGradesAdminForm(forms.ModelForm):
    """Input form for subsection grade enabling, allowing us to verify data."""

    class Meta(object):
        model = CoursePersistentGradesFlag
        fields = '__all__'

    def clean_course_id(self):
        """
        Validate the course id
        """
        return clean_course_id(self)
