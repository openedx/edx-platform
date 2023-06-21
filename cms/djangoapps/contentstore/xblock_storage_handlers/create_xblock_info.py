import logging
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import (User)  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.timezone import timezone
from django.utils.translation import gettext as _
from edx_django_utils.plugins import pluggable_override
from openedx_events.content_authoring.data import DuplicatedXBlockData
from openedx_events.content_authoring.signals import XBLOCK_DUPLICATED
from edx_proctoring.api import (
    does_backend_support_onboarding,
    get_exam_by_content_id,
    get_exam_configuration_dashboard_url,
)
from edx_proctoring.exceptions import ProctoredExamNotFoundException
from help_tokens.core import HelpUrlExpert
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from opaque_keys.edx.locator import LibraryUsageLocator
from pytz import UTC
from xblock.core import XBlock
from xblock.fields import Scope

from cms.djangoapps.contentstore.config.waffle import SHOW_REVIEW_RULES_FLAG
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from common.djangoapps.edxmako.services import MakoService
from common.djangoapps.static_replace import replace_static_urls
from common.djangoapps.student.auth import (
    has_studio_read_access,
    has_studio_write_access,
)
from common.djangoapps.util.date_utils import get_default_time_display
from common.djangoapps.util.json_request import JsonResponse, expect_json
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from openedx.core.djangoapps.bookmarks import api as bookmarks_api
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE
from openedx.core.lib.gating import api as gating_api
from openedx.core.toggles import ENTRANCE_EXAMS
from xmodule.course_block import (
    DEFAULT_START_DATE,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.library_tools import (
    LibraryToolsService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import (
    EdxJSONEncoder,
    ModuleStoreEnum,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.draft_and_published import (
    DIRECT_ONLY_CATEGORIES,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import (
    InvalidLocationError,
    ItemNotFoundError,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.inheritance import (
    own_metadata,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.services import (
    ConfigurationService,
    SettingsService,
    TeamsConfigurationService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.tabs import (
    CourseTabList,
)  # lint-amnesty, pylint: disable=wrong-import-order

from ..utils import (
    ancestor_has_staff_lock,
    find_release_date_source,
    find_staff_lock_source,
    get_split_group_display_name,
    get_user_partition_info,
    get_visibility_partition_info,
    has_children_visible_to_specific_partition_groups,
    is_currently_visible_to_students,
    is_self_paced,
)

from .create_xblock import create_xblock
from .usage_key_with_run import usage_key_with_run
from ..helpers import (
    get_parent_xblock,
    import_staged_content_from_user_clipboard,
    is_unit,
    xblock_primary_child_category,
    xblock_studio_url,
    xblock_type_display_name,
)

from .helpers import (
    NEVER,
    _filter_entrance_exam_grader,
    _get_release_date,
    _compute_visibility_state,
    is_self_paced,
    _get_gating_info,
    _was_xblock_ever_exam_linked_with_external,
    VisibilityState,
)


def _create_xblock_ancestor_info(
    xblock, course_outline=False, include_child_info=False, is_concise=False
):
    """
    Returns information about the ancestors of an xblock. Note that the direct parent will also return
    information about all of its children.
    """
    ancestors = []

    def collect_ancestor_info(ancestor, include_child_info=False, is_concise=False):
        """
        Collect xblock info regarding the specified xblock and its ancestors.
        """
        if ancestor:
            direct_children_only = lambda parent: parent == ancestor
            ancestors.append(
                create_xblock_info(
                    ancestor,
                    include_child_info=include_child_info,
                    course_outline=course_outline,
                    include_children_predicate=direct_children_only,
                    is_concise=is_concise,
                )
            )
            collect_ancestor_info(get_parent_xblock(ancestor), is_concise=is_concise)

    collect_ancestor_info(
        get_parent_xblock(xblock),
        include_child_info=include_child_info,
        is_concise=is_concise,
    )
    return {"ancestors": ancestors}


def _create_xblock_child_info(
    xblock,
    course_outline,
    graders,
    include_children_predicate=NEVER,
    user=None,
    course=None,
    is_concise=False,
):
    """
    Returns information about the children of an xblock, as well as about the primary category
    of xblock expected as children.
    """
    child_info = {}
    child_category = xblock_primary_child_category(xblock)
    if child_category:
        child_info = {
            "category": child_category,
            "display_name": xblock_type_display_name(
                child_category, default_display_name=child_category
            ),
        }
    if xblock.has_children and include_children_predicate(xblock):
        child_info["children"] = [
            create_xblock_info(
                child,
                include_child_info=True,
                course_outline=course_outline,
                include_children_predicate=include_children_predicate,
                parent_xblock=xblock,
                graders=graders,
                user=user,
                course=course,
                is_concise=is_concise,
            )
            for child in xblock.get_children()
        ]
    return child_info


@pluggable_override("OVERRIDE_CREATE_XBLOCK_INFO")
def create_xblock_info(  # lint-amnesty, pylint: disable=too-many-statements
    xblock,
    data=None,
    metadata=None,
    include_ancestor_info=False,
    include_child_info=False,
    course_outline=False,
    include_children_predicate=NEVER,
    parent_xblock=None,
    graders=None,
    user=None,
    course=None,
    is_concise=False,
):
    """
    Creates the information needed for client-side XBlockInfo.

    If data or metadata are not specified, their information will not be added
    (regardless of whether or not the xblock actually has data or metadata).

    There are three optional boolean parameters:
      include_ancestor_info - if true, ancestor info is added to the response
      include_child_info - if true, direct child info is included in the response
      is_concise - if true, returns the concise version of xblock info, default is false.
      course_outline - if true, the xblock is being rendered on behalf of the course outline.
        There are certain expensive computations that do not need to be included in this case.

    In addition, an optional include_children_predicate argument can be provided to define whether or
    not a particular xblock should have its children included.

    You can customize the behavior of this function using the `OVERRIDE_CREATE_XBLOCK_INFO` pluggable override point.
    For example:
    >>> def create_xblock_info(default_fn, xblock, *args, **kwargs):
    ...     xblock_info = default_fn(xblock, *args, **kwargs)
    ...     xblock_info['icon'] = xblock.icon_override
    ...     return xblock_info
    """
    is_library_block = isinstance(xblock.location, LibraryUsageLocator)
    is_xblock_unit = is_unit(xblock, parent_xblock)
    # this should not be calculated for Sections and Subsections on Unit page or for library blocks
    has_changes = None
    if (is_xblock_unit or course_outline) and not is_library_block:
        has_changes = modulestore().has_changes(xblock)

    if graders is None:
        if not is_library_block:
            graders = CourseGradingModel.fetch(xblock.location.course_key).graders
        else:
            graders = []

    # Filter the graders data as needed
    graders = _filter_entrance_exam_grader(graders)

    # We need to load the course in order to retrieve user partition information.
    # For this reason, we load the course once and re-use it when recursively loading children.
    if course is None:
        course = modulestore().get_course(xblock.location.course_key)

    # Compute the child info first so it can be included in aggregate information for the parent
    should_visit_children = include_child_info and (
        course_outline and not is_xblock_unit or not course_outline
    )
    if should_visit_children and xblock.has_children:
        child_info = _create_xblock_child_info(
            xblock,
            course_outline,
            graders,
            include_children_predicate=include_children_predicate,
            user=user,
            course=course,
            is_concise=is_concise,
        )
    else:
        child_info = None

    release_date = _get_release_date(xblock, user)

    if xblock.category != "course" and not is_concise:
        visibility_state = _compute_visibility_state(
            xblock, child_info, is_xblock_unit and has_changes, is_self_paced(course)
        )
    else:
        visibility_state = None
    published = (
        modulestore().has_published_version(xblock) if not is_library_block else None
    )
    published_on = (
        get_default_time_display(xblock.published_on)
        if published and xblock.published_on
        else None
    )

    # defining the default value 'True' for delete, duplicate, drag and add new child actions
    # in xblock_actions for each xblock.
    xblock_actions = {
        "deletable": True,
        "draggable": True,
        "childAddable": True,
        "duplicable": True,
    }
    explanatory_message = None

    # is_entrance_exam is inherited metadata.
    if xblock.category == "chapter" and getattr(xblock, "is_entrance_exam", None):
        # Entrance exam section should not be deletable, draggable and not have 'New Subsection' button.
        xblock_actions["deletable"] = xblock_actions["childAddable"] = xblock_actions[
            "draggable"
        ] = False
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)

        # Translators: The {pct_sign} here represents the percent sign, i.e., '%'
        # in many languages. This is used to avoid Transifex's misinterpreting of
        # '% o'. The percent sign is also translatable as a standalone string.
        explanatory_message = _(
            "Students must score {score}{pct_sign} or higher to access course materials."
        ).format(
            score=int(parent_xblock.entrance_exam_minimum_score_pct * 100),
            # Translators: This is the percent sign. It will be used to represent
            # a percent value out of 100, e.g. "58%" means "58/100".
            pct_sign=_("%"),
        )

    xblock_info = {
        "id": str(xblock.location),
        "display_name": xblock.display_name_with_default,
        "category": xblock.category,
        "has_children": xblock.has_children,
    }

    if course is not None and PUBLIC_VIDEO_SHARE.is_enabled(xblock.location.course_key):
        xblock_info.update(
            {
                "video_sharing_enabled": True,
                "video_sharing_options": course.video_sharing_options,
                "video_sharing_doc_url": HelpUrlExpert.the_one().url_for_token(
                    "social_sharing"
                ),
            }
        )

    if xblock.category == "course":
        discussions_config = DiscussionsConfiguration.get(course.id)
        show_unit_level_discussions_toggle = (
            discussions_config.enabled
            and discussions_config.supports_in_context_discussions()
            and discussions_config.enable_in_context
            and discussions_config.unit_level_visibility
        )
        xblock_info["unit_level_discussions"] = show_unit_level_discussions_toggle

    if is_concise:
        if child_info and child_info.get("children", []):
            xblock_info["child_info"] = child_info
        # Groups are labelled with their internal ids, rather than with the group name. Replace id with display name.
        group_display_name = get_split_group_display_name(xblock, course)
        xblock_info["display_name"] = (
            group_display_name if group_display_name else xblock_info["display_name"]
        )
    else:
        user_partitions = get_user_partition_info(xblock, course=course)
        xblock_info.update(
            {
                "edited_on": get_default_time_display(xblock.subtree_edited_on)
                if xblock.subtree_edited_on
                else None,
                "published": published,
                "published_on": published_on,
                "studio_url": xblock_studio_url(xblock, parent_xblock),
                "released_to_students": datetime.now(UTC) > xblock.start,
                "release_date": release_date,
                "visibility_state": visibility_state,
                "has_explicit_staff_lock": xblock.fields[
                    "visible_to_staff_only"
                ].is_set_on(xblock),
                "start": xblock.fields["start"].to_json(xblock.start),
                "graded": xblock.graded,
                "due_date": get_default_time_display(xblock.due),
                "due": xblock.fields["due"].to_json(xblock.due),
                "relative_weeks_due": xblock.relative_weeks_due,
                "format": xblock.format,
                "course_graders": [grader.get("type") for grader in graders],
                "has_changes": has_changes,
                "actions": xblock_actions,
                "explanatory_message": explanatory_message,
                "group_access": xblock.group_access,
                "user_partitions": user_partitions,
                "show_correctness": xblock.show_correctness,
            }
        )

        if xblock.category == "sequential":
            xblock_info.update(
                {
                    "hide_after_due": xblock.hide_after_due,
                }
            )
        elif xblock.category in ("chapter", "course"):
            if xblock.category == "chapter":
                xblock_info.update(
                    {
                        "highlights": xblock.highlights,
                    }
                )
            elif xblock.category == "course":
                xblock_info.update(
                    {
                        "highlights_enabled_for_messaging": course.highlights_enabled_for_messaging,
                    }
                )
            xblock_info.update(
                {
                    # used to be controlled by a waffle switch, now just always enabled
                    "highlights_enabled": True,
                    # used to be controlled by a waffle flag, now just always disabled
                    "highlights_preview_only": False,
                    "highlights_doc_url": HelpUrlExpert.the_one().url_for_token(
                        "content_highlights"
                    ),
                }
            )

        # update xblock_info with special exam information if the feature flag is enabled
        if settings.FEATURES.get("ENABLE_SPECIAL_EXAMS"):
            if xblock.category == "course":
                xblock_info.update(
                    {
                        "enable_proctored_exams": xblock.enable_proctored_exams,
                        "create_zendesk_tickets": xblock.create_zendesk_tickets,
                        "enable_timed_exams": xblock.enable_timed_exams,
                    }
                )
            elif xblock.category == "sequential":
                rules_url = settings.PROCTORING_SETTINGS.get("LINK_URLS", {}).get(
                    "online_proctoring_rules", ""
                )
                supports_onboarding = does_backend_support_onboarding(
                    course.proctoring_provider
                )

                proctoring_exam_configuration_link = None
                if xblock.is_proctored_exam:
                    proctoring_exam_configuration_link = (
                        get_exam_configuration_dashboard_url(
                            course.id, xblock_info["id"]
                        )
                    )

                if course.proctoring_provider == "proctortrack":
                    show_review_rules = SHOW_REVIEW_RULES_FLAG.is_enabled(
                        xblock.location.course_key
                    )
                else:
                    show_review_rules = True

                xblock_info.update(
                    {
                        "is_proctored_exam": xblock.is_proctored_exam,
                        "was_exam_ever_linked_with_external": _was_xblock_ever_exam_linked_with_external(
                            course, xblock
                        ),
                        "online_proctoring_rules": rules_url,
                        "is_practice_exam": xblock.is_practice_exam,
                        "is_onboarding_exam": xblock.is_onboarding_exam,
                        "is_time_limited": xblock.is_time_limited,
                        "exam_review_rules": xblock.exam_review_rules,
                        "default_time_limit_minutes": xblock.default_time_limit_minutes,
                        "proctoring_exam_configuration_link": proctoring_exam_configuration_link,
                        "supports_onboarding": supports_onboarding,
                        "show_review_rules": show_review_rules,
                    }
                )

        # Update with gating info
        xblock_info.update(_get_gating_info(course, xblock))
        if is_xblock_unit:
            # if xblock is a Unit we add the discussion_enabled option
            xblock_info["discussion_enabled"] = xblock.discussion_enabled
        if xblock.category == "sequential":
            # Entrance exam subsection should be hidden. in_entrance_exam is
            # inherited metadata, all children will have it.
            if getattr(xblock, "in_entrance_exam", False):
                xblock_info["is_header_visible"] = False

        if data is not None:
            xblock_info["data"] = data
        if metadata is not None:
            xblock_info["metadata"] = metadata
        if include_ancestor_info:
            xblock_info["ancestor_info"] = _create_xblock_ancestor_info(
                xblock, course_outline, include_child_info=True
            )
        if child_info:
            xblock_info["child_info"] = child_info
        if visibility_state == VisibilityState.staff_only:
            xblock_info["ancestor_has_staff_lock"] = ancestor_has_staff_lock(
                xblock, parent_xblock
            )
        else:
            xblock_info["ancestor_has_staff_lock"] = False

        if course_outline:
            if xblock_info["has_explicit_staff_lock"]:
                xblock_info["staff_only_message"] = True
            elif child_info and child_info["children"]:
                xblock_info["staff_only_message"] = all(
                    child["staff_only_message"] for child in child_info["children"]
                )
            else:
                xblock_info["staff_only_message"] = False

            xblock_info[
                "has_partition_group_components"
            ] = has_children_visible_to_specific_partition_groups(xblock)
        xblock_info["user_partition_info"] = get_visibility_partition_info(
            xblock, course=course
        )

    return xblock_info
