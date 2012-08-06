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


def check_permissions(user, content, per):
    """
    Accepts a list of permissions and proceed if any of the permission is valid.
    Note that check_permissions("can_view", "can_edit") will proceed if the user has either
    "can_view" or "can_edit" permission. To use AND operator in between, wrap them in 
    a list:
        check_permissions(["can_view", "can_edit"])

    Special conditions can be used like permissions, e.g. 
        (["can_vote", "open"])  # where open is True if not content['closed']
    """
    permissions = filter(lambda x: len(x), list(per))

    def test_permission(user, permission, operator="or"):
        if isinstance(permission, basestring):
            # import pdb; pdb.set_trace()
            if permission == "":
                return True
            elif permission == "author":
                return content["user_id"] == str(user.id)
            elif permission == "open":
                return not content["closed"]
            return has_permission(user, permission)
        elif isinstance(permission, list) and operator in ["and", "or"]:
            results = [test_permission(user, x, operator="and") for x in permission]
            if operator == "or":
                return True in results
            elif operator == "and":
                return not False in results

    return test_permission(user, permissions, operator="or")


VIEW_PERMISSIONS = {
    'update_thread'     :       ('edit_content', ['update_thread', 'open', 'author']),
    'create_comment'    :       (["create_comment", "open"]),
    'delete_thread'     :       ('delete_thread'),
    'update_comment'    :       ('edit_content', ['update_comment', 'open', 'author']),
    'endorse_comment'   :       ('endorse_comment'),
    'openclose_thread'  :       ('openclose_thread'),
    'create_sub_comment':       (['create_sub_comment', 'open']),
    'delete_comment'    :       ('delete_comment'),
    'vote_for_commend'  :       (['vote', 'open']),
    'undo_vote_for_comment':    (['unvote', 'open']),
    'vote_for_thread'   :       (['vote', 'open']),
    'undo_vote_for_thread':     (['unvote', 'open']),
    'follow_thread'     :       ('follow_thread'),
    'follow_commentable':       ('follow_commentable'),
    'follow_user'       :       ('follow_user'),
    'unfollow_thread'   :       ('unfollow_thread'),
    'unfollow_commentable':     ('unfollow_commentable'),
    'unfollow_user'     :       ('unfollow_user'),
    'create_thread'     :       ('create_thread'),
}

def check_permissions_by_view(user, content, name):
    try:
        p = VIEW_PERMISSIONS[name]
    except KeyError:
        logging.warning("Permission for view named %s does not exist in permissions.py" % name)
    permissions = list((p, ) if isinstance(p, basestring) else p)
    return check_permissions(user, content, permissions)


moderator_role = Role.register("Moderator")
student_role = Role.register("Student")

moderator_role.register_permissions(["edit_content", "delete_thread", "openclose_thread",
                                    "endorse_comment", "delete_comment"])
student_role.register_permissions(["vote", "update_thread", "follow_thread", "unfollow_thread",
                                   "update_comment", "create_sub_comment", "unvote" , "create_thread",
                                   "follow_commentable", "unfollow_commentable", "create_comment", ])

moderator_role.inherit_permissions(student_role)