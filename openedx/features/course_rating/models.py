"""
Content Rating Models
"""
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class CourseRating(TimeStampedModel):
    """
    CourseRating model.
    """
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE)
    course = CourseKeyField(max_length=255, db_index=True)
    rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(User, null=True, blank=True, related_name='moderator', on_delete=models.CASCADE)

    def __str__(self):
        return '{user}: ({course} - {rating})'.format(
            user=self.user.username,
            course=self.course,
            rating=self.rating
        )


@receiver(post_delete, sender=CourseRating, dispatch_uid='update_course_avg_rating')
@receiver(post_save, sender=CourseRating, dispatch_uid='update_course_avg_rating')
def update_course_avg_rating(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
   Update course average rating.
   """
    course_ratings = CourseRating.objects.filter(course=instance.course).values_list('rating', flat=True)
    total_raters = len(course_ratings)

    course_avg_rating, __ = CourseAverageRating.objects.get_or_create(
        course=instance.course
    )
    course_avg_rating.average_rating = sum(course_ratings) / total_raters
    course_avg_rating.total_raters = total_raters
    course_avg_rating.save()


class CourseAverageRating(TimeStampedModel):
    """
    CourseAverageRating model.
    """
    course = CourseKeyField(max_length=255, db_index=True, blank=True)
    average_rating = models.DecimalField(default=0.0, max_digits=30, decimal_places=2)
    total_raters = models.IntegerField(default=0)

    def __str__(self):
        return '{course}: ({average_rating} - {total_raters})'.format(
            course=self.course,
            average_rating=self.average_rating,
            total_raters=self.total_raters
        )
