import logging

from django.db import models
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.db.models.signals import post_save

from student.models import CourseEnrollment

from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor

FORUM_ROLE_ADMINISTRATOR = 'Administrator'
FORUM_ROLE_MODERATOR = 'Moderator'
FORUM_ROLE_COMMUNITY_TA = 'Community TA'
FORUM_ROLE_STUDENT = 'Student'


@receiver(post_save, sender=CourseEnrollment)
def assign_default_role(sender, instance, **kwargs):
    # The code below would remove all forum Roles from a user when they unenroll
    # from a course. Concerns were raised that it should apply only to students,
    # or that even the history of student roles is important for research
    # purposes. Since this was new functionality being added in this release,
    # I'm just going to comment it out for now and let the forums team deal with
    # implementing the right behavior.
    #
    # # We've unenrolled the student, so remove all roles for this course
    # if not instance.is_active:
    #     course_roles = list(Role.objects.filter(course_id=instance.course_id))
    #     instance.user.roles.remove(*course_roles)
    #     return

    # We've enrolled the student, so make sure they have the Student role
    role = Role.objects.get_or_create(course_id=instance.course_id, name="Student")[0]
    instance.user.roles.add(role)


class Role(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False)
    users = models.ManyToManyField(User, related_name="roles")
    course_id = models.CharField(max_length=255, blank=True, db_index=True)

    class Meta:
        # use existing table that was originally created from django_comment_client app
        db_table = 'django_comment_client_role'

    def __unicode__(self):
        return self.name + " for " + (self.course_id if self.course_id else "all courses")

    def inherit_permissions(self, role):   # TODO the name of this method is a little bit confusing,
                                         # since it's one-off and doesn't handle inheritance later
        if role.course_id and role.course_id != self.course_id:
            logging.warning("%s cannot inherit permissions from %s due to course_id inconsistency", \
                            self, role)
        for per in role.permissions.all():
            self.add_permission(per)

    def add_permission(self, permission):
        self.permissions.add(Permission.objects.get_or_create(name=permission)[0])

    def has_permission(self, permission):
        course_loc = CourseDescriptor.id_to_location(self.course_id)
        course = modulestore().get_instance(self.course_id, course_loc)
        if self.name == FORUM_ROLE_STUDENT and \
           (permission.startswith('edit') or permission.startswith('update') or permission.startswith('create')) and \
           (not course.forum_posts_allowed):
            return False

        return self.permissions.filter(name=permission).exists()


class Permission(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, primary_key=True)
    roles = models.ManyToManyField(Role, related_name="permissions")

    class Meta:
        # use existing table that was originally created from django_comment_client app
        db_table = 'django_comment_client_permission'

    def __unicode__(self):
        return self.name
