"""
Admin for managing the connection to the Forums backend service.
"""
from django.contrib import admin

from .models import CourseForumsProfanityCheckerConfig, ForumsConfig

admin.site.register(ForumsConfig)
admin.site.register(CourseForumsProfanityCheckerConfig)
