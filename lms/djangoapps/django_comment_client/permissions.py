from .models import Role, Permission
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

def has_permission(user, p):
    if not Permission.objects.filter(name=p).exists():
        logging.warning("Permission %s was not registered. " % p)
    if Permission.objects.filter(users=user, name=p).exists():
        return True
    if Permission.objects.filter(roles__in=user.roles.all(), name=p).exists():
        return True
    return False

def has_permissions(user, *args):
    for p in args:
        if not has_permission(user, p):
            return False
    return True

def add_permission(instance, p):
    permission = Permission.register(name=p)
    if isinstance(instance, User) or isinstance(isinstance, Role):
        instance.permissions.add(permission)
    else:
        raise TypeError("Permission can only be added to a role or user")


@receiver(post_save, sender=User)
def assign_default_role(sender, instance, **kwargs):
    # if kwargs.get("created", True):
    role = moderator_role if instance.is_staff else student_role
    logging.info("assign_default_role: adding %s as %s" % (instance, role))
    instance.roles.add(role)

moderator_role = Role.register("Moderator")
student_role = Role.register("Student")

moderator_role.register_permissions(["edit_content", "delete_thread", "openclose_thread",
                                     "update_thread", "endorse_comment", "delete_comment"])
student_role.register_permissions(["vote", "update_thread", "follow_thread", "unfollow_thread",
                                   "update_comment", "create_sub_comment", "unvote" , "create_thread",
                                   "follow_commentable", "unfollow_commentable", "create_comment", ])

moderator_role.inherit_permissions(student_role)