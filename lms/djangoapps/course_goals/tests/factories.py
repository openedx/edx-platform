"""Provides factories for course goals."""

import factory
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_goals.models import CourseGoal, CourseGoalReminderStatus, UserActivity
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


class CourseGoalFactory(DjangoModelFactory):
    """Factory for CourseGoal, which will make user and course for you"""
    class Meta:
        model = CourseGoal

    class Params:
        overview = factory.SubFactory(CourseOverviewFactory)

    user = factory.SubFactory(UserFactory)
    course_key = factory.SelfAttribute('overview.id')


class CourseGoalReminderStatusFactory(DjangoModelFactory):
    """Factory for CourseGoalReminderStatus"""
    class Meta:
        model = CourseGoalReminderStatus

    goal = factory.SubFactory(CourseGoalFactory)


class UserActivityFactory(DjangoModelFactory):
    """Factory for UserActivity"""
    class Meta:
        model = UserActivity

    user = factory.SubFactory(UserFactory)
