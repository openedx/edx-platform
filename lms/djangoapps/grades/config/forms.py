"""
Defines a form for providing validation of subsection grade templates.
"""


import logging

from django import forms

from lms.djangoapps.grades.config.models import CoursePersistentGradesFlag
from openedx.core.lib.courses import clean_course_id

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
