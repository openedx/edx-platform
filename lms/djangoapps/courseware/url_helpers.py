"""
Module to define url helpers functions
"""


import six
from django.conf import settings
from django.urls import reverse
from six.moves.urllib.parse import urlencode

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


def get_microfrontend_url(course_key, sequence_key=None, unit_key=None):
    """
    Return a str with the URL for the specified content in the Courseware MFE.

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

    http://localhost:2000/course-v1:edX+DemoX+Demo_Course/block-v1:edX+DemoX+Demo_Course+type@sequential+block@19a30717eff543078a5d94ae9d6c18a5/block-v1:edX+DemoX+Demo_Course+type@vertical+block@4a1bba2a403f40bca5ec245e945b0d76

    `course_key`, `sequence_key`, and `unit_key` can be either OpaqueKeys or
    strings. They're only ever used to concatenate a URL string.
    """
    mfe_link = '{}/course/{}'.format(settings.LEARNING_MICROFRONTEND_URL, course_key)

    if sequence_key:
        mfe_link += '/{}'.format(sequence_key)

        if unit_key:
            mfe_link += '/{}'.format(unit_key)

    return mfe_link
