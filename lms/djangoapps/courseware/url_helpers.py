"""
Module to define url helpers functions
"""
from __future__ import absolute_import

import six
from django.urls import reverse
from six.moves.urllib.parse import urlencode  # pylint: disable=import-error

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import navigation_index, path_to_location


def get_redirect_url(course_key, usage_key):
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
    ) = path_to_location(modulestore(), usage_key)

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
