from django.db import models


class TargetCourse(models.Model):
    """
    These courses are marked for data extraction.

    @course_id: (string) id of the course
    """
    course_id = models.TextField(max_length=255)

    def __unicode__(self):
        return '{}'.format(self.course_id)