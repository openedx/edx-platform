from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
import json


class CustomSettings(models.Model):
    """
    Extra Custom Settings for each course
    """
    id = CourseKeyField(max_length=255, db_index=True, primary_key=True)
    is_featured = models.BooleanField(default=False)
    show_grades = models.BooleanField(default=True)
    enable_enrollment_email = models.BooleanField(default=True)
    auto_enroll = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, null=True, blank=True)
    course_short_id = models.IntegerField(null=False, unique=True)
    seo_tags = models.TextField(null=True, blank=True)
    course_open_date = models.DateTimeField(null=True)

    class Meta:
        app_label = 'custom_settings'

    def __unicode__(self):
        return '{} | {}'.format(self.id, self.is_featured)

    def save(self, *args, **kwargs):
        # This means that the model isn't saved to the database yet
        if self._state.adding and not self.course_short_id:
            # Get the maximum course_short_id value from the database
            last_id = CustomSettings.objects.all().aggregate(largest=models.Max('course_short_id'))['largest']

            # aggregate can return None! Check it first.
            # If it isn't none, just use the last ID specified (which should be the greatest) and add one to it
            if last_id is not None:
                course_short_id = last_id + 1
                self.course_short_id = course_short_id

            else:
                self.course_short_id = 100

        super(CustomSettings, self).save(*args, **kwargs)

    def get_course_meta_tags(self):
        """
        :return:
            get seo tags for course
        """
        title, description, keywords, robots, utm_params = "", "", "", "", {}
        if self.seo_tags:
            _json_tags = json.loads(self.seo_tags)
            title = _json_tags.get("title", title)
            description = _json_tags.get("description", description)
            keywords = _json_tags.get("keywords", keywords)
            robots = _json_tags.get("robots", robots)
            utm_params = {key: _json_tags[key] for key in _json_tags.keys() if 'utm_' in key}

        return {
            "title": title,
            "description": description,
            "keywords": keywords,
            "robots": robots,
            "utm_params": utm_params
        }
