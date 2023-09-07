"""
Models for course roles schema
"""
from django.contrib.auth import get_user_model
from django.db import models

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from organizations.models import Organization

User = get_user_model()


class CourseRolesRole(models.Model):
    """
    Model for a course roles role.

    A role is a collection of permissions that can be assigned to a user.
    The Service field defines for which service UI the role is intended, such as CMS or LMS.

    """
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255)
    long_description = models.TextField()
    service = models.ForeignKey('CourseRolesService', on_delete=models.DO_NOTHING, null=True)
    permissions = models.ManyToManyField('CourseRolesPermission', through='CourseRolesRolePermissions')
    users = models.ManyToManyField(User, through='CourseRolesUserRole')

    def __str__(self):
        return self.name


class CourseRolesPermission(models.Model):
    """
    Model for a course roles permission.

    A permission represents what a user can do.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CourseRolesRolePermissions(models.Model):
    """
    Model for a course roles role permission.

    A role permission is a mapping between a role and a permission.
    """
    role = models.ForeignKey('CourseRolesRole', on_delete=models.CASCADE)
    permission = models.ForeignKey('CourseRolesPermission', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.role} - {self.permission}"


class CourseRolesUserRole(models.Model):
    """
    Model for a course roles user role.

    A user role is a mapping between a user, a role, a course and an organization,
    if the course is null then the user role is a global role for the organization.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey('CourseRolesRole', on_delete=models.CASCADE)
    course = models.ForeignKey(
        CourseOverview,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        null=True,
    )
    org = models.ForeignKey(Organization, on_delete=models.DO_NOTHING, null=False)

    class Meta:
        unique_together = ('user', 'role', 'course')

    def __str__(self):
        return f"{self.user} - {self.course} - {self.role}"


class CourseRolesService(models.Model):
    """
    Model for a course roles service.

    A service is a UI that can be used to assign roles to users.
    Such as CMS or LMS.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
