import logging

from django.db import models
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.db.models.signals import post_save

from student.models import CourseEnrollment

from courseware.courses import get_course_by_id

FORUM_ROLE_ADMINISTRATOR = 'Administrator'
FORUM_ROLE_MODERATOR = 'Moderator'
FORUM_ROLE_COMMUNITY_TA = 'Community TA'
FORUM_ROLE_STUDENT = 'Student'


@receiver(post_save, sender=CourseEnrollment)
def assign_default_role(sender, instance, **kwargs):
    if instance.user.is_staff:
        role = Role.objects.get_or_create(course_id=instance.course_id, name="Moderator")[0]
    else:
        role = Role.objects.get_or_create(course_id=instance.course_id, name="Student")[0]

    logging.info("assign_default_role: adding %s as %s" % (instance.user, role))
    instance.user.roles.add(role)


class Role(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False)
    users = models.ManyToManyField(User, related_name="roles")
    course_id = models.CharField(max_length=255, blank=True, db_index=True)

    def __unicode__(self):
        return self.name + " for " + (self.course_id if self.course_id else "all courses")

    def inherit_permissions(self, role): # TODO the name of this method is a little bit confusing,
                                         # since it's one-off and doesn't handle inheritance later
        if role.course_id and role.course_id != self.course_id:
            logging.warning("{0} cannot inherit permissions from {1} due to course_id inconsistency", \
                            self, role)
        for per in role.permissions.all():
            self.add_permission(per)

    def add_permission(self, permission):
        self.permissions.add(Permission.objects.get_or_create(name=permission)[0])

    def has_permission(self, permission):
        course = get_course_by_id(self.course_id)
        if self.name == FORUM_ROLE_STUDENT and \
           (permission.startswith('edit') or permission.startswith('update') or permission.startswith('create')) and \
           (not course.forum_posts_allowed):
            return False
        
        return self.permissions.filter(name=permission).exists()


class Permission(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, primary_key=True)
    roles = models.ManyToManyField(Role, related_name="permissions")

    def __unicode__(self):
        return self.name


@receiver(post_save, sender=CourseEnrollment)
def assign_default_role(sender, instance, **kwargs):
    if instance.user.is_staff:
        role = Role.objects.get_or_create(course_id=instance.course_id, name="Moderator")[0]
    else:
        role = Role.objects.get_or_create(course_id=instance.course_id, name="Student")[0]

    logging.info("assign_default_role: adding %s as %s" % (instance.user, role))
    instance.user.roles.add(role)
