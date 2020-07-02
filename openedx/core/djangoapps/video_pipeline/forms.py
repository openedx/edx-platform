"""
Defines a form to provide validations for course-specific configuration.
"""
from django import forms

from openedx.core.djangoapps.video_config.forms import CourseSpecificFlagAdminBaseForm
from openedx.core.djangoapps.video_pipeline.models import CourseVideoUploadsEnabledByDefault


class CourseVideoUploadsEnabledByDefaultAdminForm(CourseSpecificFlagAdminBaseForm):
    """
    Form for course-specific Video Uploads enabled by default configuration.
    """

    class Meta(object):
        model = CourseVideoUploadsEnabledByDefault
        fields = '__all__'


class VEMPipelineIntegrationAdminForm(forms.ModelForm):
    """
    Form for VEM Pipeline Integration Admin class
    """

    def clean_vem_enabled_courses_percentage(self):
        """
        Validates that vem_enabled_courses_percentage lies between 0 to 100.
        """
        vem_enabled_courses_percentage = self.cleaned_data['vem_enabled_courses_percentage']
        if vem_enabled_courses_percentage < 0 or vem_enabled_courses_percentage > 100:
            raise forms.ValidationError('Invalid percentage, the value must be between 0 and 100')
        return vem_enabled_courses_percentage
