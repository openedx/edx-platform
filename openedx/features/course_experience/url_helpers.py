"""
Helper functions for logic related to learning (courseare & course home) URLs.

Centralizdd in openedx/features/course_experience instead of lms/djangoapps/courseware
because the Studio course outline may need these utilities.
"""
from typing import Optional, Tuple

import six
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey, UsageKey
from six.moves.urllib.parse import urlencode

from lms.djangoapps.courseware.toggles import courseware_mfe_is_active
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import navigation_index, path_to_location

User = get_user_model()


def get_courseware_url(
        usage_key: UsageKey,
        request: Optional[HttpRequest] = None,
) -> str:
    """
    Return the URL to the canonical learning experience for a given block.

    We choose between either the Legacy frontend or Learning MFE depending on the
    course that the block is in, the requesting user, and the state of
    the 'courseware' waffle flags.

    If you know that you want a Learning MFE URL, regardless of configuration,
    then it is more performant to call `get_learning_mfe_courseware_url` directly.

    Raises:
        * ItemNotFoundError if no data at the `usage_key`.
        * NoPathToItem if we cannot build a path to the `usage_key`.
    """
    course_key = usage_key.course_key.replace(version_guid=None, branch=None)
    if courseware_mfe_is_active(course_key):
        sequence_key, unit_key = _get_sequence_and_unit_keys(
            usage_key=usage_key,
            request=request,
        )
        return get_learning_mfe_courseware_url(
            course_key=course_key,
            sequence_key=sequence_key,
            unit_key=unit_key,
        )
    else:
        return get_legacy_courseware_url(
            usage_key=usage_key,
            request=request
        )


def _get_sequence_and_unit_keys(
        usage_key: UsageKey,
        request: Optional[HttpRequest] = None,
) -> Tuple[Optional[UsageKey], Optional[UsageKey]]:
    """
    Find the sequence and unit containg a block within a course run.

    Performance consideration: Currently, this function incurs a modulestore query.

    Raises:
        * ItemNotFoundError if no data at the `usage_key`.
        * NoPathToItem if we cannot build a path to the `usage_key`.

    Returns: (sequence_key|None, unit_key|None)
    * sequence_key points to a Section (ie chapter) or Subsection (ie sequential).
    * unit_key points to  Unit (ie vertical).
    Either of these may be None if we are above that level in the course hierarchy.
    For example, if `usage_key` points to a Subsection, then unit_key will be None.
    """
    path = path_to_location(modulestore(), usage_key, request, full_path=True)
    if len(path) <= 1:
        # Course-run-level block:
        # We have no Sequence or Unit to return.
        return None, None
    elif len(path) == 2:
        # Section-level (ie chapter) block:
        # The Section is the Sequence. We have no Unit to return.
        return path[1], None
    elif len(path) == 3:
        # Subsection-level block:
        # The Subsection is the Sequence. We still have no Unit to return.
        return path[2], None
    else:
        # Unit-level (or lower) block:
        # The Subsection is the Sequence, and the next level down is the Unit.
        return path[2], path[3]


def get_legacy_courseware_url(
        usage_key: UsageKey,
        request: Optional[HttpRequest] = None,
) -> str:
    """
    Return the URL to Legacy (LMS-rendered) courseware content.

    Raises:
        * ItemNotFoundError if no data at the usage_key.
        * NoPathToItem if location not in any class.
    """
    (
        course_key, chapter, section, vertical_unused,
        position, final_target_id
    ) = path_to_location(modulestore(), usage_key, request)

    # choose the appropriate view (and provide the necessary args) based on the
    # args provided by the redirect.
    # Rely on index to do all error handling and access control.
    if chapter is None:
        redirect_url = reverse('courseware', args=(six.text_type(course_key), ))
    elif section is None:
        redirect_url = reverse('courseware_chapter', args=(six.text_type(course_key), chapter))
    elif position is None:
        redirect_url = reverse(
            'courseware_section',
            args=(six.text_type(course_key), chapter, section)
        )
    else:
        # Here we use the navigation_index from the position returned from
        # path_to_location - we can only navigate to the topmost vertical at the
        # moment
        redirect_url = reverse(
            'courseware_position',
            args=(six.text_type(course_key), chapter, section, navigation_index(position))
        )
    redirect_url += "?{}".format(urlencode({'activate_block_id': six.text_type(final_target_id)}))
    return redirect_url


def get_learning_mfe_courseware_url(
        course_key: CourseKey,
        sequence_key: Optional[UsageKey] = None,
        unit_key: Optional[UsageKey] = None,
) -> str:
    """
    Return a str with the URL for the specified courseware content in the Learning MFE.

    The micro-frontend determines the user's position in the vertical via
    a separate API call, so all we need here is the course_key, sequence, and
    vertical IDs to format it's URL. For simplicity and performance reasons,
    this method does not inspect the modulestore to try to figure out what
    Unit/Vertical a sequence is in. If you try to pass in a unit_key without
    a sequence_key, the value will just be ignored and you'll get a URL pointing
    to just the course_key.

    Note that `sequence_key` may either point to a Section (ie chapter) or
    Subsection (ie sequential), as those are both abstractly understood as
    "sequences". If you pass in a Section-level `sequence_key`, then the MFE
    will replace it with key of the first Subsection in that Section.

    It is also capable of determining our section and vertical if they're not
    present.  Fully specifying it all is preferable, though, as the
    micro-frontend can save itself some work, resulting in a better user
    experience.

    We're building a URL like this:

    http://localhost:2000/course/course-v1:edX+DemoX+Demo_Course/block-v1:edX+DemoX+Demo_Course+type@sequential+block@19a30717eff543078a5d94ae9d6c18a5/block-v1:edX+DemoX+Demo_Course+type@vertical+block@4a1bba2a403f40bca5ec245e945b0d76

    `course_key`, `sequence_key`, and `unit_key` can be either OpaqueKeys or
    strings. They're only ever used to concatenate a URL string.
    """
    mfe_link = '{}/course/{}'.format(settings.LEARNING_MICROFRONTEND_URL, course_key)

    if sequence_key:
        mfe_link += '/{}'.format(sequence_key)

        if unit_key:
            mfe_link += '/{}'.format(unit_key)

    return mfe_link


def get_learning_mfe_home_url(
        course_key: CourseKey, view_name: Optional[str] = None
) -> str:
    """
    Given a course run key and view name, return the appropriate course home (MFE) URL.

    We're building a URL like this:

    http://localhost:2000/course/course-v1:edX+DemoX+Demo_Course/dates

    `course_key` can be either an OpaqueKey or a string.
    `view_name` is an optional string.
    """
    mfe_link = f'{settings.LEARNING_MICROFRONTEND_URL}/course/{course_key}'

    if view_name:
        mfe_link += f'/{view_name}'

    return mfe_link


def is_request_from_learning_mfe(request: HttpRequest):
    """
    Returns whether the given request was made by the frontend-app-learning MFE.
    """
    return (
        settings.LEARNING_MICROFRONTEND_URL and
        request.META.get('HTTP_REFERER', '').startswith(settings.LEARNING_MICROFRONTEND_URL)
    )
