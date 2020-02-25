"""
Module to define url helpers functions
"""


import six
from django.conf import settings
from django.urls import reverse
from six.moves.urllib.parse import urlencode  # pylint: disable=import-error

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import navigation_index, path_to_location


def get_redirect_url(course_key, usage_key, request=None):
    """ Returns the redirect url back to courseware

    Args:
        course_id(str): Course Id string
        location(str): The location id of course component

    Raises:
        ItemNotFoundError if no data at the location or NoPathToItem if location not in any class

    Returns:
        Redirect url string
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


def get_microfrontend_redirect_url(course_key, path=None):
    """
    The micro-frontend determines the user's position in the vertical via
    a separate API call, so all we need here is the course_key, section, and vertical
    IDs to format it's URL.

    It is also capable of determining our section and vertical if they're not present.  Fully
    specifying it all is preferable, though, as the micro-frontend can save itself some work,
    resulting in a better user experience.

    We're building a URL like this:

    http://localhost:2000/course-v1:edX+DemoX+Demo_Course/block-v1:edX+DemoX+Demo_Course+type@sequential+block@19a30717eff543078a5d94ae9d6c18a5/block-v1:edX+DemoX+Demo_Course+type@vertical+block@4a1bba2a403f40bca5ec245e945b0d76
    """

    redirect_url = '{base_url}/{prefix}/{course_key}'.format(
        base_url=settings.LEARNING_MICROFRONTEND_URL,
        prefix='course',
        course_key=course_key
    )

    if path is None:
        return redirect_url

    # The first four elements of the path list are the ones we care about here:
    # - course
    # - chapter
    # - sequence
    # - vertical
    # We skip course because we already have it from our argument above, and we skip chapter
    # because the micro-frontend URL doesn't include it.
    if len(path) > 2:
        redirect_url += '/{sequence_key}'.format(
            sequence_key=path[2]
        )
    if len(path) > 3:
        redirect_url += '/{vertical_key}'.format(
            vertical_key=path[3]
        )

    return redirect_url
