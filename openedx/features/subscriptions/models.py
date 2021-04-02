from logging import getLogger

from datetime import date

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from student.models import CourseEnrollment

logger = getLogger(__name__)


class UserSubscription(TimeStampedModel):
    """
    The "UserSubscription" model.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_id = models.PositiveIntegerField(db_index=True)
    expiration_date = models.DateField(default=None, null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)

    LIMITED_ACCESS = 'limited-access'
    FULL_ACCESS_COURSES = 'full-access-courses'
    FULL_ACCESS_TIME_PERIOD = 'full-access-time-period'
    LIFETIME_ACCESS = 'lifetime-access'

    SUBSCRIPTION_TYPE_CHOICES = (
        (LIMITED_ACCESS, 'Limited Access', ),
        (FULL_ACCESS_COURSES, 'Full Access (Courses)', ),
        (FULL_ACCESS_TIME_PERIOD, 'Full Access (Time period)', ),
        (LIFETIME_ACCESS, 'Lifetime Access', ),
    )

    subscription_type = models.CharField(choices=SUBSCRIPTION_TYPE_CHOICES, max_length=30)
    max_allowed_courses = models.PositiveIntegerField(
        help_text=_(
            'Maximum number of courses allowed to enroll in paid tracks using the subscription.'
        ),
        null=True,
        blank=True
    )
    course_enrollments = models.ManyToManyField(CourseEnrollment, blank=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    def __str__(self):
        return "Subscription of type {subscription_type} with ID {subscription_id} for User {user_email}".format(
            subscription_type=self.subscription_type,
            subscription_id=self.subscription_id,
            user_email=self.user.username,
        )

    @property
    def is_active(self):
        """
        Get active status of a subscription.

        Check if a subscription is active even if a user can no longer purchase a new course through it.
        """
        course_enrollments_count = self.course_enrollments.count()
        if self.expiration_date and self.max_allowed_courses:
            return self.expiration_date >= date.today() and course_enrollments_count <= self.max_allowed_courses
        elif self.expiration_date and not self.max_allowed_courses:
            return self.expiration_date >= date.today()
        elif self.max_allowed_courses and not self.expiration_date:
            return course_enrollments_count <= self.max_allowed_courses

        return True

    @property
    def is_valid(self):
        """
        Get validity status of a subscription.

        Check if a user can enroll in a new course through this subscription.
        """
        course_enrollments_count = self.course_enrollments.count()
        if self.subscription_type == self.LIFETIME_ACCESS:
            return True
        elif self.subscription_type == self.FULL_ACCESS_COURSES:
            return self.expiration_date >= date.today()
        elif self.subscription_type == self.FULL_ACCESS_TIME_PERIOD:
            return course_enrollments_count < self.max_allowed_courses
        elif self.subscription_type == self.LIMITED_ACCESS:
            return self.expiration_date >= date.today() and course_enrollments_count < self.max_allowed_courses

    @classmethod
    def get_valid_subscriptions(self, site, username=None):
        """
        Get valid subscriptions of a user.

        Returns:
            queryset: Returns latest valid user subscription.
        """
        filter_params = {
            'site': site
        }
        if username:
            filter_params['user__username'] = username

        user_subscriptions = self.objects.filter(**filter_params)
        valid_user_subscriptions = filter(lambda subscription: subscription.is_valid, user_subscriptions)
        valid_user_subscriptions_ids = [subscription.subscription_id for subscription in valid_user_subscriptions]
        if len(valid_user_subscriptions_ids) > 1:
            logger.warning('Valid subscription count exceeds 1.')

        return user_subscriptions.filter(subscription_id__in=valid_user_subscriptions_ids).order_by('-created')


class UserSubscriptionHistory(TimeStampedModel):
    """
    The "UserSubscriptionHistory" model to maintain a history of changes in "UserSubscription" model.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_id = models.PositiveIntegerField()
    expiration_date = models.DateField(default=None, null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)

    LIMITED_ACCESS = 'limited-access'
    FULL_ACCESS_COURSES = 'full-access-courses'
    FULL_ACCESS_TIME_PERIOD = 'full-access-time-period'
    LIFETIME_ACCESS = 'lifetime-access'

    SUBSCRIPTION_TYPE_CHOICES = (
        (LIMITED_ACCESS, 'Limited Access', ),
        (FULL_ACCESS_COURSES, 'Full Access (Courses)', ),
        (FULL_ACCESS_TIME_PERIOD, 'Full Access (Time period)', ),
        (LIFETIME_ACCESS, 'Lifetime Access', ),
    )

    subscription_type = models.CharField(choices=SUBSCRIPTION_TYPE_CHOICES, max_length=30)
    max_allowed_courses = models.PositiveIntegerField(
        help_text=_(
            'Maximum number of courses allowed to enroll in paid tracks using the subscription.'
        ),
        null=True,
        blank=True
    )
    course_enrollments = models.ManyToManyField(CourseEnrollment, blank=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)

    def __str__(self):
        return "Subscription of type {subscription_type} with ID {subscription_id} for User {user_email}".format(
            subscription_type=self.subscription_type,
            subscription_id=self.subscription_id,
            user_email=self.user.username,
        )

@receiver(post_save, sender=UserSubscription)
def update_user_subscription_history(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Add user subscription changes to user subscription history.

    Arguments:
        sender(UserSubscription class): sender of the signal
        instance(UserSubscription): instance associated with the current signal
    """
    user_subscription_history = UserSubscriptionHistory.objects.create(
        site=instance.site,
        user=instance.user,
        subscription_id=instance.subscription_id,
        expiration_date=instance.expiration_date,
        subscription_type=instance.subscription_type,
        description=instance.description,
        max_allowed_courses=instance.max_allowed_courses
    )
    for course_enrollment in instance.course_enrollments.all():
        user_subscription_history.course_enrollments.add(course_enrollment)
