from django.db import models


class CourseDataExtraction(models.Model):
    """
    These courses are marked for data extraction. These will be used to determine data of which courses is to be extracted

    @course_id: (string) id of the course. can be gotten through to_deprecated_string() method of CourseKey object
    """
    class Meta:
        app_label = 'data_extract'

    course_id = models.CharField(max_length=255)
    emails = models.TextField()

    def __unicode__(self):
        return '{}'.format(self.course_id)
