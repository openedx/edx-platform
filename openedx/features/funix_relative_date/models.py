from django.db import models

class FunixRelativeDate(models.Model):
    user_id = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)
    block_id = models.EmailField(max_length=255)
    type = models.EmailField(max_length=255)
    index = models.IntegerField()

    def __str__(self):
        return "%s %s" % (self.user_id, self.course_id)
