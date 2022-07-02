from django.db import models
from django.db.models import Q
from django.utils.timezone import now
from common.djangoapps.student.models import get_user_by_id
from common.djangoapps.student.models import CourseEnrollment


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
        return FunixRelativeDate.objects.filter(
            user_id=user_id,
            course_id=course_id
        )

    @classmethod
    def get_enroll_date_by_id(self, user_id, course_id):
        try:
            enrollment =  FunixRelativeDate.objects.get(user_id=user_id, course_id=course_id, type="start")

            return enrollment.date
        except:
            try:
                user = get_user_by_id(user_id)
                enrollment = CourseEnrollment.get_enrollment(user, course_id)

                return enrollment.created
            except:
                return None
        return None



    @classmethod
    def get_all_enroll_by_course(self, course_id):
        return FunixRelativeDate.objects.filter(
            course_id=course_id,
            type='start'
        )
