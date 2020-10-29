"""
Forms for configuring courses for verified track cohorting
"""


from django import forms
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.verified_track_content.models import VerifiedTrackCohortedCourse
from xmodule.modulestore.django import modulestore


class VerifiedTrackCourseForm(forms.ModelForm):
    """Validate course keys for the VerifiedTrackCohortedCourse model

    The default behavior in Django admin is to:
    * Save course keys for courses that do not exist.
    * Return a 500 response if the course key format is invalid.

    Using this form ensures that we display a user-friendly
    error message instead.

    """
    class Meta(object):
        model = VerifiedTrackCohortedCourse
        fields = '__all__'

    def clean_course_key(self):
        """Validate the course key.

        Checks that the key format is valid and that
        the course exists.  If not, displays an error message.

        Arguments:
            field_name (str): The name of the field to validate.

        Returns:
            CourseKey

        """
        cleaned_id = self.cleaned_data['course_key']
        error_msg = _('COURSE NOT FOUND.  Please check that the course ID is valid.')

        try:
            course_key = CourseKey.from_string(cleaned_id)
        except InvalidKeyError:
            raise forms.ValidationError(error_msg)

        if not modulestore().has_course(course_key):
            raise forms.ValidationError(error_msg)

        return course_key
