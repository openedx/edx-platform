from django.db import models
from django.db.models import Q
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
    def delete_all_date(self, user_id, course_id):
        return FunixRelativeDate.objects.filter(
            ~Q(type='start'),
            user_id=user_id,
            course_id=course_id
        ).delete()

    @classmethod
    def get_all_block_by_id(self, user_id, course_id):
        print('-----------get_all_block_by_id:',FunixRelativeDate.objects.filter(
            user_id=user_id,
            course_id=course_id
        ) )
        return FunixRelativeDate.objects.filter(
            user_id=user_id,
            course_id=course_id
        )

    @classmethod
    def get_enroll_by_id(self, user_id, course_id):
        return FunixRelativeDate.objects.filter(user_id=user_id, course_id=course_id, type="start")[0]

    @classmethod
    def get_all_enroll_by_course(self, course_id):
        return FunixRelativeDate.objects.filter(
            course_id=course_id,
            type='start'
        )
