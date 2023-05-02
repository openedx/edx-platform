from django.db.models.signals import post_save
from django.dispatch import receiver

from common.djangoapps.student.models import CourseEnrollment


@receiver(post_save, sender='student.CourseEnrollment')
def course_enrollment_post_save(sender, instance, created, **kwargs):
    breakpoint()
    if created:
        breakpoint()

# post_save.connect(course_enrollment_post_save, sender=CourseEnrollment)
