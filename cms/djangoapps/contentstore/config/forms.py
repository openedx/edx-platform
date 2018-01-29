"""
Defines a form for providing validation.
"""
import logging

from django import forms
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from six import text_type

from contentstore.config.models import CourseNewAssetsPageFlag
from openedx.core.lib.courses import clean_course_id
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class CourseNewAssetsPageAdminForm(forms.ModelForm):
    """Input form for new asset page enablement, allowing us to verify user input."""

    class Meta(object):
        model = CourseNewAssetsPageFlag
        fields = '__all__'

    def clean_course_id(self):
        """
        Validate the course id
        """
        return clean_course_id(self)
