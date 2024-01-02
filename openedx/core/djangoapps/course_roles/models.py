"""
Models for course roles schema
"""
from django.conf import settings
from django.db import models

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from organizations.models import Organization


class Role(models.Model):
    """
    Model for a role.

    A role is a collection of permissions that can be assigned to a user.
    The services field defines in which service UI the role is intended to be assigned, such as CMS and/or LMS.

    """
    name = models.CharField(max_length=255, unique=True)
    services = models.ManyToManyField('Service', through='RoleService')
    permissions = models.ManyToManyField('Permission', through='RolePermission')
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='UserRole')

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    Model for a permission.

    A permission represents what a user can do.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """
    Model for a role permission.

    A role permission is a mapping between a role and a permission.
    """
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    permission = models.ForeignKey('Permission', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['role', 'permission'], name='course_roles__rolepermission_uniq_idx')
        ]

    def __str__(self):
        return f"{self.role} - {self.permission}"


class UserRole(models.Model):
    """
    Model for a user role.

    A user role is a mapping between a user, a role, a course and an organization.
    If the course is null, the user role assignment is in use for all courses that belong to the organization.
    If the course and the organization are null,
    the user role assignment is in use for all courses that belong to the instance.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    course = models.ForeignKey(
        CourseOverview,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'role', 'course'], name='course_roles__urserrole_uniq_idx')
        ]

    def __str__(self):
        return f"{self.user} - {self.role} - {self.course} - {self.org}"


class Service(models.Model):
    """
    Model for a service.

    A service is a UI that can be used to assign roles to users.
    Such as CMS or LMS.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class RoleService(models.Model):
    """
    Model for a role service.

    A role service is a mapping between a role and a service.
    """
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['role', 'service'], name='course_roles__roleservice_uniq_idx')
        ]

    def __str__(self):
        return f"{self.role} - {self.service}"
