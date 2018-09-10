from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CustomSettings(models.Model):
    """
    Extra Custom Settings for each course
    """
    id = CourseKeyField(max_length=255, db_index=True, primary_key=True)
    is_featured = models.BooleanField(default=False)
    show_grades = models.BooleanField(default=True)
    tags = models.CharField(max_length=255, null=True, blank=True)
    course_short_id = models.IntegerField(null=False, unique=True)

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

        super(CustomSettings, self).save(*args, **kwargs)
