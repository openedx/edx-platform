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
    tags = models.CharField(max_length=255, null=True, blank=True)
    seo_tags = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '{} | {}'.format(self.id, self.is_featured)

    def get_course_meta_tags(self):
        """
        :return:
            get seo tags for course
        """
        title, description, keywords, robots = "", "", "", ""
        if self.seo_tags:
            _json_tags = json.loads(self.seo_tags)
            title = _json_tags.get("title", "")
            description = _json_tags.get("description", "")
            keywords = _json_tags.get("keywords", "")
            robots = _json_tags.get("robots", "")

        return {
            "title": title,
            "description": description,
            "keywords": keywords,
            "robots": robots
        }
