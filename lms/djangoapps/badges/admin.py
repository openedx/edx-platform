"""
Admin registration for Badge Models
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from lms.djangoapps.badges.models import (
    BadgeAssertion,
    BadgeClass,
    CourseCompleteImageConfiguration,
    CourseEventBadgesConfiguration
)

admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeClass)
admin.site.register(BadgeAssertion)
# Use the standard Configuration Model Admin handler for this model.
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)
