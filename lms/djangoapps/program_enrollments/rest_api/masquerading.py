"""
TODO
"""
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils.functional import cached_property

log = logging.getLogger(__name__)


class MasqueradableMixin:
    """
    Mixin for views that may be able to support masquerading.

    This mixin does not actually implement masquerading -- that would be done
    in MST-109 and MST-209. However, it allows views to write code that is easily
    adaptable to masquerading by providing a 'target_user' property, which is calculated
    based on the value of the 'target_username_kwarg' URL parameter.

    Instead of referencing `self.request.user`, views implementing this mixin should
    base its operations on `self.target_user`. When masquerading is active,
    `self.target_user` would refer to the user we are masquerading as.

    Currently, PermissionDenied is raised if `self.target_user` is not identical to
    `self.request.user`.
    """
    target_username_kwarg = "username"

    @cached_property
    def target_user(self):
        """
        Get user to perform operations as.

        This will generally be the requesting user, but in the case of masquerading,
        it will be a different user.

        Raises: PermssionDenied, if:
            1. target user does not exist,
            2. requesting user is *not* global staff, or
            3. target user *is* global staff.
        Scenarios 1-3 are not differentiated to the requesting user (to avoid
        information leak) but are exposed in the logs.
        """
        _User = get_user_model()
        requester = self.request.user
        target_username = self.request.kwargs[self.target_username_kwarg]
        cannot_masquerade_message = (
            "User {requester.username} "
            "cannot perform operations on behalf of {target_username}"
        ).format(requester=requester, target_username=target_username)
        try:
            target = _User.objects.get(username=target_username)
        except _User.DoesNotExist:
            log.info(
                "%s, as %s does not exist.",
                cannot_masquerade_message,
                target_username,
            )
            raise PermissionDenied(cannot_masquerade_message)
        if target != requester:
            log.info(
                "%s, as masquerading is not yet enabled in the program_enrollments API."
                cannot_masquerade_message,
            )
            raise PermissionDenied(cannot_masquerade_message)
        if not requester.is_staff:
            log.info(
                "%s, as %s is not global staff.",
                cannot_masquerade_message,
                requester.username,
            )
            raise PermissionDenied(cannot_masquerade_message)
        if target.is_staff:
            log.info(
                "%s, as %s is global staff.",
                cannot_masquerade_message,
                target_username,
            )
            raise PermissionDenied(cannot_masquerade_message)
        return target
