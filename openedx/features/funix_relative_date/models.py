from django.db import models
from django.utils.timezone import now

class FunixRelativeDate(models.Model):
    user_id = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)
    block_id = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=255)
    date = 	models.DateField(default=now, editable=False)
    index = models.IntegerField()

    def __str__(self):
        return "%s %s %s" % (self.user_id, self.course_id, self.block_id)

class FunixRelativeDateDAO():
    @classmethod
    def get_block_by_id(self, user_id, course_id, block_id):
        return FunixRelativeDate.objects.get(user_id=user_id, course_id=course_id, block_id=block_id)

    @classmethod
    def get_enroll_by_id(self, user_id, course_id):
        print('43-23', user_id, course_id)
        return FunixRelativeDate.objects.get(user_id=user_id, course_id=course_id, type="start")
