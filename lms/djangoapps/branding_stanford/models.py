"""
Model for branding_stanford

This was implemented initially so that the list of course tiles could be
stored in this model.
"""
from django.db import models

from config_models.models import ConfigurationModel
from xmodule_django.models import CourseKeyField


class TileConfiguration(ConfigurationModel):
    """
        Stores a list of tiles presented on the front page.
    """
    site = models.CharField(max_length=32, default='default', blank=False)
    course_id = CourseKeyField(max_length=255, db_index=True)

    class Meta(ConfigurationModel.Meta):
        app_label = 'branding_stanford'

    def __unicode__(self):
        return u"{0} {1} {2}".format(self.site, self.course_id, self.enabled)
