"""
Defines a form to provide validations for course-specific configuration.
"""

from openedx.core.djangoapps.video_config.forms import CourseSpecificFlagAdminBaseForm
from openedx.core.djangoapps.video_pipeline.models import CourseVideoUploadsEnabledByDefault


class CourseVideoUploadsEnabledByDefaultAdminForm(CourseSpecificFlagAdminBaseForm):
    """
    Form for course-specific Video Uploads enabled by default configuration.
    """

    class Meta(object):
        model = CourseVideoUploadsEnabledByDefault
        fields = '__all__'
