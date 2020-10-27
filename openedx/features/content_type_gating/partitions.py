"""
Define the ContentTypeGatingPartition and ContentTypeGatingPartitionScheme.

These are used together to allow course content to be blocked for a subset
of audit learners.
"""

import logging

import crum
from django.apps import apps
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from web_fragments.fragment import Fragment

from course_modes.models import CourseMode
from lms.djangoapps.commerce.utils import EcommerceService
from xmodule.partitions.partitions import UserPartition, UserPartitionError
from openedx.core.lib.mobile_utils import is_request_from_mobile_app
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.content_type_gating.helpers import CONTENT_GATING_PARTITION_ID, FULL_ACCESS, LIMITED_ACCESS

LOG = logging.getLogger(__name__)

CONTENT_TYPE_GATING_SCHEME = "content_type_gate"


def create_content_gating_partition(course):
    """
    Create and return the Content Gating user partition.
    """

    enabled_for_course = ContentTypeGatingConfig.enabled_for_course(course_key=course.id)
    studio_override_for_course = ContentTypeGatingConfig.current(course_key=course.id).studio_override_enabled
    if not (enabled_for_course or studio_override_for_course):
        return None

    try:
        content_gate_scheme = UserPartition.get_scheme(CONTENT_TYPE_GATING_SCHEME)
    except UserPartitionError:
        LOG.warning(
            "No %r scheme registered, ContentTypeGatingPartitionScheme will not be created.",
            CONTENT_TYPE_GATING_SCHEME
        )
        return None

    used_ids = set(p.id for p in course.user_partitions)
    if CONTENT_GATING_PARTITION_ID in used_ids:
        # It's possible for course authors to add arbitrary partitions via XML import. If they do, and create a
        # partition with id 51, it will collide with the Content Gating Partition. We'll catch that here, and
        # then fix the course content as needed (or get the course team to).
        LOG.warning(
            "Can't add %r partition, as ID %r is assigned to %r in course %s.",
            CONTENT_TYPE_GATING_SCHEME,
            CONTENT_GATING_PARTITION_ID,
            _get_partition_from_id(course.user_partitions, CONTENT_GATING_PARTITION_ID).name,
            unicode(course.id),
        )
        return None

    partition = content_gate_scheme.create_user_partition(
        id=CONTENT_GATING_PARTITION_ID,
        name=_(u"Feature-based Enrollments"),
        description=_(u"Partition for segmenting users by access to gated content types"),
        parameters={"course_id": unicode(course.id)}
    )
    return partition


class ContentTypeGatingPartition(UserPartition):
    """
    A custom UserPartition which allows us to override the access denied messaging in regards
    to gated content.
    """
    def access_denied_fragment(self, block, user, user_group, allowed_groups):
        modes = CourseMode.modes_for_course_dict(block.scope_ids.usage_id.course_key)
        verified_mode = modes.get(CourseMode.VERIFIED)
        if verified_mode is None or not self._is_audit_enrollment(user, block):
            return None
        ecommerce_checkout_link = self._get_checkout_link(user, verified_mode.sku)

        request = crum.get_current_request()
        frag = Fragment(render_to_string('content_type_gating/access_denied_message.html', {
            'mobile_app': is_request_from_mobile_app(request),
            'ecommerce_checkout_link': ecommerce_checkout_link,
            'min_price': str(verified_mode.min_price)
        }))
        return frag

    def access_denied_message(self, block, user, user_group, allowed_groups):
        if self._is_audit_enrollment(user, block):
            return _(u"Graded assessments are available to Verified Track learners. Upgrade to Unlock.")
        return None

    def _is_audit_enrollment(self, user, block):
        course_enrollment = apps.get_model('student.CourseEnrollment')
        mode_slug, is_active = course_enrollment.enrollment_mode_for_user(user, block.scope_ids.usage_id.course_key)
        return mode_slug == CourseMode.AUDIT and is_active

    def _get_checkout_link(self, user, sku):
        ecomm_service = EcommerceService()
        ecommerce_checkout = ecomm_service.is_enabled(user)
        if ecommerce_checkout and sku:
            return ecomm_service.get_checkout_page_url(sku) or ''


class ContentTypeGatingPartitionScheme(object):
    """
    This scheme implements the Content Type Gating permission partitioning.

    This partitioning is roughly the same as the verified/audit split, but also allows for individual
    schools or courses to specify particular learner subsets by email that are allowed to access
    the gated content despite not being verified users.
    """

    read_only = True

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition, **kwargs):  # pylint: disable=unused-argument
        """
        Returns the Group for the specified user.
        """

        # For now, treat everyone as a Full-access user, until we have the rest of the
        # feature gating logic in place.

        if not ContentTypeGatingConfig.enabled_for_enrollment(user=user, course_key=course_key,
                                                              user_partition=user_partition):
            return FULL_ACCESS

        # If CONTENT_TYPE_GATING is enabled use the following logic to determine whether a user should have FULL_ACCESS
        # or LIMITED_ACCESS

        course_mode = apps.get_model('course_modes.CourseMode')
        modes = course_mode.modes_for_course(course_key, include_expired=True, only_selectable=False)
        modes_dict = {mode.slug: mode for mode in modes}

        # If there is no verified mode, all users are granted FULL_ACCESS
        if not course_mode.has_verified_mode(modes_dict):
            return FULL_ACCESS

        course_enrollment = apps.get_model('student.CourseEnrollment')

        mode_slug, is_active = course_enrollment.enrollment_mode_for_user(user, course_key)

        if mode_slug and is_active:
            course_mode = course_mode.mode_for_course(
                course_key,
                mode_slug,
                modes=modes,
            )
            if course_mode is None:
                LOG.error(
                    "User %s is in an unknown CourseMode '%s'"
                    " for course %s. Granting full access to content for this user",
                    user.username,
                    mode_slug,
                    course_key,
                )
                return FULL_ACCESS

            if mode_slug == CourseMode.AUDIT:
                return LIMITED_ACCESS
            else:
                return FULL_ACCESS
        else:
            # Unenrolled users don't get gated content
            return LIMITED_ACCESS

    @classmethod
    def create_user_partition(cls, id, name, description, groups=None, parameters=None, active=True):  # pylint: disable=redefined-builtin, invalid-name, unused-argument
        """
        Create a custom UserPartition to support dynamic groups.

        A Partition has an id, name, scheme, description, parameters, and a list
        of groups. The id is intended to be unique within the context where these
        are used. (e.g., for partitions of users within a course, the ids should
        be unique per-course). The scheme is used to assign users into groups.
        The parameters field is used to save extra parameters e.g., location of
        the course ID for this partition scheme.

        Partitions can be marked as inactive by setting the "active" flag to False.
        Any group access rule referencing inactive partitions will be ignored
        when performing access checks.
        """
        return ContentTypeGatingPartition(
            id,
            unicode(name),
            unicode(description),
            [
                LIMITED_ACCESS,
                FULL_ACCESS,
            ],
            cls,
            parameters,
            # N.B. This forces Content Type Gating partitioning to always be active on every course,
            # no matter how the course xml content is set. We will manage enabling/disabling
            # as a policy in the LMS.
            active=True,
        )


def _get_partition_from_id(partitions, user_partition_id):
    """
    Look for a user partition with a matching id in the provided list of partitions.

    Returns:
        A UserPartition, or None if not found.
    """
    for partition in partitions:
        if partition.id == user_partition_id:
            return partition

    return None
