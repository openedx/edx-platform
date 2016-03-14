"""
Store status messages in the database.
"""

from django.db import models
from django.contrib import admin
from django.core.cache import cache

from xmodule_django.models import CourseKeyField

from config_models.models import ConfigurationModel
from config_models.admin import ConfigurationModelAdmin


class GlobalStatusMessage(ConfigurationModel):
    """
    Model that represents the current status message.
    """
    message = models.TextField(blank=True, null=True)

    def full_message(self, course_key):
        """ Returns the full status message, including any course-specific status messages. """
        cache_key = "status_message.{course_id}".format(course_id=unicode(course_key))
        if cache.get(cache_key):
            return cache.get(cache_key)

        msg = self.message
        if course_key:
            try:
                course_message = self.coursemessage_set.get(course_key=course_key)
                # Don't add the message if course_message is blank.
                if course_message:
                    msg = u"{} <br /> {}".format(msg, course_message.message)
            except CourseMessage.DoesNotExist:
                # We don't have a course-specific message, so pass.
                pass
        cache.set(cache_key, msg)
        return msg

    def __unicode__(self):
        return "{} - {} - {}".format(self.change_date, self.enabled, self.message)


class CourseMessage(models.Model):
    """
    Model that allows the user to specify messages for individual courses.

    This is not a ConfigurationModel because using it's not designed to support multiple configurations at once,
    which would be problematic if separate courses need separate error messages.
    """
    global_message = models.ForeignKey(GlobalStatusMessage)
    course_key = CourseKeyField(max_length=255, blank=True, db_index=True)
    message = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.course_key)


admin.site.register(GlobalStatusMessage, ConfigurationModelAdmin)
admin.site.register(CourseMessage)
