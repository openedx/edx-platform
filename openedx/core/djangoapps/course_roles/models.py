"""
Models for course roles schema
"""
from django.db import models


class CourseRolesRole(models.Model):
    """
    Model for a course role.
    """
    class RoleType(models.TextChoices):
        """
        Enum for the role type.
        """
        DEFAULT = 'default'
        CUSTOM = 'custom'
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255)
    long_description = models.TextField()
    type = models.CharField(max_length=64, choices=RoleType.choices, default=RoleType.DEFAULT)
    service = models.ForeignKey('CourseRolesService', on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.name


class CourseRolesPermission(models.Model):
    """
    Model for a course roles permission.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CourseRolesRolePermissions(models.Model):
    """
    Model for a course roles role permission.
    """
    role = models.ForeignKey('CourseRolesRole', on_delete=models.CASCADE)
    permission = models.ManyToManyField('CourseRolesPermission')
    allowed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.role} - {self.permission}"


class CourseRolesService(models.Model):
    """
    Model for a course roles service.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
