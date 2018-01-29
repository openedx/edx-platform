"""
Defines a form for providing validation of LTI consumer course-specific configuration.
"""
import logging

from django import forms
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator

from openedx.core.lib.courses import clean_course_id
from xblock_config.models import CourseEditLTIFieldsEnabledFlag
from xmodule.modulestore.django import modulestore

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
