"""
Defines a form for providing validation of LTI consumer course-specific configuration.
"""


import logging

from django import forms

from cms.djangoapps.xblock_config.models import CourseEditLTIFieldsEnabledFlag
from openedx.core.lib.courses import clean_course_id

log = logging.getLogger(__name__)


class CourseEditLTIFieldsEnabledAdminForm(forms.ModelForm):
    """
    Form for LTI consumer course-specific configuration to verify the course id.
    """

    class Meta(object):
        model = CourseEditLTIFieldsEnabledFlag
        fields = '__all__'

    def clean_course_id(self):
        """
        Validate the course id
        """
        return clean_course_id(self)
