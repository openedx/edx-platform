"""
Django database models supporting the progress app
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Q

from model_utils.models import TimeStampedModel
from xmodule_django.models import CourseKeyField


class StudentProgress(TimeStampedModel):
    """
    StudentProgress is essentially a container used to store calculated progress of user
    """
    user = models.ForeignKey(User, db_index=True)
    course_id = CourseKeyField(db_index=True, max_length=255, blank=True)
    completions = models.IntegerField(default=0)

    class Meta:
        """
        Meta information for this Django model
        """
        unique_together = (('user', 'course_id'),)

    @classmethod
    def get_total_completions(cls, course_key, exclude_users=None, org_ids=None):
        """
        Returns count of completions for a given course.
        """
        queryset = cls.objects.filter(course_id__exact=course_key, user__is_active=True)\
            .exclude(user__id__in=exclude_users)
        if org_ids:
            queryset = queryset.filter(user__organizations__in=org_ids)
        completions = queryset.aggregate(total=Sum('completions'))
        completions = completions['total'] or 0
        return completions

    @classmethod
    def get_num_users_started(cls, course_key, exclude_users=None, org_ids=None):
        """
        Returns count of users who completed at least one module.
        """
        queryset = cls.objects.filter(course_id__exact=course_key, user__is_active=True)\
            .exclude(user__id__in=exclude_users)
        if org_ids:
            queryset = queryset.filter(user__organizations__in=org_ids)
        return queryset.count()

    @classmethod
    def get_user_position(cls, course_key, user_id, exclude_users=None):
        """
        Returns user's progress position and completions for a given course.
        data = {"completions": 22, "position": 4}
        """
        data = {"completions": 0, "position": 0}
        try:
            queryset = cls.objects.get(course_id__exact=course_key, user__id=user_id)
        except cls.DoesNotExist:
            queryset = None

        if queryset:
            user_completions = queryset.completions
            user_time_completed = queryset.modified

            users_above = cls.objects.filter(Q(completions__gt=user_completions) | Q(completions=user_completions,
                                                                                     modified__lt=user_time_completed),
                                             course_id__exact=course_key, user__is_active=True)\
                .exclude(user__id__in=exclude_users)\
                .count()
            data['position'] = users_above + 1
            data['completions'] = user_completions
        return data

    @classmethod
    def generate_leaderboard(cls, course_key, count=3, exclude_users=None, org_ids=None):
        """
        Assembles a data set representing the Top N users, by progress, for a given course.

        data = [
                {'id': 123, 'username': 'testuser1', 'title', 'Engineer', 'avatar_url': 'http://gravatar.com/123/', 'completions': 0.92},
                {'id': 983, 'username': 'testuser2', 'title', 'Analyst', 'avatar_url': 'http://gravatar.com/983/', 'completions': 0.91},
                {'id': 246, 'username': 'testuser3', 'title', 'Product Owner', 'avatar_url': 'http://gravatar.com/246/', 'completions': 0.90},
                {'id': 357, 'username': 'testuser4', 'title', 'Director', 'avatar_url': 'http://gravatar.com/357/', 'completions': 0.89},
        ]

        """
        queryset = cls.objects\
            .filter(course_id__exact=course_key, user__is_active=True).exclude(user__id__in=exclude_users)
        if org_ids:
            queryset = queryset.filter(user__organizations__in=org_ids)
        queryset = queryset.values(
            'user__id',
            'user__username',
            'user__profile__title',
            'user__profile__avatar_url',
            'completions')\
            .order_by('-completions', 'modified')[:count]
        return queryset


class StudentProgressHistory(TimeStampedModel):
    """
    A running audit trail for the StudentProgress model.  Listens for
    post_save events and creates/stores copies of progress entries.
    """
    user = models.ForeignKey(User, db_index=True)
    course_id = CourseKeyField(db_index=True, max_length=255, blank=True)
    completions = models.IntegerField()
