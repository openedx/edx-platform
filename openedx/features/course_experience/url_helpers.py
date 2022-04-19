"""
Helper functions for logic related to learning (courseare & course home) URLs.

Centralized in openedx/features/course_experience instead of lms/djangoapps/courseware
because the Studio course outline may need these utilities.
"""
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.http.request import QueryDict
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey, UsageKey
from six.moves.urllib.parse import urlencode, urlparse

from lms.djangoapps.courseware.toggles import courseware_mfe_is_active
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.search import navigation_index, path_to_location  # lint-amnesty, pylint: disable=wrong-import-order

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

    If redirecting to a specific Sequence or Sequence/Unit in a Learning MFE
    regardless of configuration, call make_learning_mfe_courseware_url directly
    for better performance.

    Raises:
        * ItemNotFoundError if no data at the `usage_key`.
        * NoPathToItem if we cannot build a path to the `usage_key`.
    """
    if courseware_mfe_is_active():
        get_url_fn = _get_new_courseware_url
    else:
        get_url_fn = _get_legacy_courseware_url
    return get_url_fn(usage_key=usage_key, request=request)


def _get_legacy_courseware_url(
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
        redirect_url = reverse('courseware', args=(str(course_key), ))
    elif section is None:
        redirect_url = reverse('courseware_chapter', args=(str(course_key), chapter))
    elif position is None:
        redirect_url = reverse(
            'courseware_section',
            args=(str(course_key), chapter, section)
        )
    else:
        # Here we use the navigation_index from the position returned from
        # path_to_location - we can only navigate to the topmost vertical at the
        # moment
        redirect_url = reverse(
            'courseware_position',
            args=(str(course_key), chapter, section, navigation_index(position))
        )
    redirect_url += "?{}".format(urlencode({'activate_block_id': str(final_target_id)}))
    return redirect_url


def _get_new_courseware_url(
        usage_key: UsageKey,
        request: Optional[HttpRequest] = None,
) -> str:
    """
    Return the URL to the "new" (Learning Micro-Frontend) experience for a given block.

    Raises:
        * ItemNotFoundError if no data at the `usage_key`.
        * NoPathToItem if we cannot build a path to the `usage_key`.
    """
    course_key = usage_key.course_key.replace(version_guid=None, branch=None)
    path = path_to_location(modulestore(), usage_key, request, full_path=True)
    if len(path) <= 1:
        # Course-run-level block:
        # We have no Sequence or Unit to return.
        sequence_key, unit_key = None, None
    elif len(path) == 2:
        # Section-level (ie chapter) block:
        # The Section is the Sequence. We have no Unit to return.
        sequence_key, unit_key = path[1], None
    elif len(path) == 3:
        # Subsection-level block:
        # The Subsection is the Sequence. We still have no Unit to return.
        sequence_key, unit_key = path[2], None
    else:
        # Unit-level (or lower) block:
        # The Subsection is the Sequence, and the next level down is the Unit.
        sequence_key, unit_key = path[2], path[3]
    return make_learning_mfe_courseware_url(
        course_key=course_key,
        sequence_key=sequence_key,
        unit_key=unit_key,
    )


def make_learning_mfe_courseware_url(
        course_key: CourseKey,
        sequence_key: Optional[UsageKey] = None,
        unit_key: Optional[UsageKey] = None,
        params: Optional[QueryDict] = None,
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
    `params` is an optional QueryDict object (e.g. request.GET)
    """
    mfe_link = f'{settings.LEARNING_MICROFRONTEND_URL}/course/{course_key}'

    if sequence_key:
        mfe_link += f'/{sequence_key}'

        if unit_key:
            mfe_link += f'/{unit_key}'

    if params:
        mfe_link += f'?{params.urlencode()}'

    return mfe_link


def get_learning_mfe_home_url(
        course_key: CourseKey,
        url_fragment: Optional[str] = None,
        params: Optional[QueryDict] = None,
) -> str:
    """
    Given a course run key and view name, return the appropriate course home (MFE) URL.

    We're building a URL like this:

    http://localhost:2000/course/course-v1:edX+DemoX+Demo_Course/dates

    `course_key` can be either an OpaqueKey or a string.
    `url_fragment` is an optional string.
    `params` is an optional QueryDict object (e.g. request.GET)
    """
    mfe_link = f'{settings.LEARNING_MICROFRONTEND_URL}/course/{course_key}'

    if url_fragment:
        mfe_link += f'/{url_fragment}'

    if params:
        mfe_link += f'?{params.urlencode()}'

    return mfe_link


def is_request_from_learning_mfe(request: HttpRequest):
    """
    Returns whether the given request was made by the frontend-app-learning MFE.
    """
    if not settings.LEARNING_MICROFRONTEND_URL:
        return False

    url = urlparse(settings.LEARNING_MICROFRONTEND_URL)
    mfe_url_base = f'{url.scheme}://{url.netloc}'
    return request.META.get('HTTP_REFERER', '').startswith(mfe_url_base)
