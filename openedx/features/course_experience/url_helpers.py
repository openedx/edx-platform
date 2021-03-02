"""
Helper functions for logic related to learning (courseare & course home) URLs.

Centralizdd in openedx/features/course_experience instead of lms/djangoapps/courseware
because the Studio course outline may need these utilities.
"""
from datetime import datetime
from typing import Optional, Tuple

import six
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey, UsageKey
from six.moves.urllib.parse import urlencode

from lms.djangoapps.courseware.toggles import courseware_mfe_is_active
from openedx.core.djangoapps.content.learning_sequences.api import get_course_outline, get_user_course_outline
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
        * ItemNotFoundError if no data at the usage_key.
        * NoPathToItem if location not in any class.
    """
    course_key = usage_key.course_key.replace(version_guid=None, branch=None)
    if courseware_mfe_is_active(course_key):
        sequence_key, unit_key = _get_sequence_and_unit_keys(
            usage_key=usage_key,
            user=(request.user if request else None),
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
        user: Optional[User] = None,
        request: Optional[HttpRequest] = None,
) -> Tuple[Optional[UsageKey], Optional[UsageKey]]:
    """
    Find the sequence and unit of a block within a course run.

    Currently requires a modulestore query.
    Could probably be further optimized.

    Raises:
        * ItemNotFoundError if no data at the usage_key.
        * NoPathToItem if location not in any class.

    Returns: (sequence_key|None, unit_key|None)
    """
    path = path_to_location(modulestore(), usage_key, request, full_path=True)
    if len(path) <= 1:
        # Course-run-level block: no sequence or unit key.
        return None, None
    elif len(path) == 2:
        # Section-level (ie chapter) block:
        # no unit key, but try to find the first sequence within the section
        # so that we can send the user there instead of the course run root.
        section_key = path[1]
        if user:
            course_sections = get_user_course_outline(
                course_key=usage_key.course_key,
                user=user,
                at_time=datetime.now(),
            ).sections
        else:
            course_sections = get_course_outline(
                course_key=usage_key.course_key
            ).sections
        try:
            # Try to find a matching section,
            # and grab the first subsection within it.
            section_data = next(
                section for section in course_sections
                if section.usage_key == section_key
            )
            return next(section_data.sequences), None
        except StopIteration:
            # Either there were no matching sections,
            # or the matching section is empty.
            return None, None
    elif len(path) == 3:
        # Subsection-level block:
        # We have a sequence key, but no unit key.
        return path[2], None
    else:
        # Unit-level (or lower) block:
        # We have both a sequence key and a unit key.
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
        course_key,
        chapter,
        section,
        _unit_id,
        position,
        final_target_id,
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
    a separate API call, so all we need here is the course_key, section, and
    vertical IDs to format it's URL. For simplicity and performance reasons,
    this method does not inspect the modulestore to try to figure out what
    Unit/Vertical a sequence is in. If you try to pass in a unit_key without
    a sequence_key, the value will just be ignored and you'll get a URL pointing
    to just the course_key.

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
