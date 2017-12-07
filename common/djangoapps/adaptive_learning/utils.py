"""
Utils for adaptive_learning app.
"""

import calendar
from dateutil import parser

from lms.djangoapps.courseware.url_helpers import get_redirect_url
from xmodule.modulestore.django import modulestore
from xmodule.library_content_module import AdaptiveLibraryContentModule


def get_pending_reviews(course, user_id):
    """
    Return pending reviews for `course` and user identified by `user_id`.

    Use API provided by `AdaptiveLibraryContentModule` to fetch a raw list of pending reviews,
    then turn it into a format optimized for reading data that is relevant for displaying revisions
    on the dashboard.

    More specifically, turn raw list of pending reviews into a dictionary
    that maps values of the 'review_question_uid' property
    to corresponding values of the 'next_review_at' property.

    - The 'review_question_uid' property of a pending review specifies the `block_id`
      of the problem to review.

    - The 'next_review_at' property of a pending review specifies the due date
      for the review.
    """
    pending_reviews = AdaptiveLibraryContentModule.fetch_pending_reviews(course, user_id)
    return {
        pending_review['review_question_uid']: pending_review['next_review_at']
        for pending_review in pending_reviews
    }


def get_revisions(course, pending_reviews):
    """
    Return list of revisions for `pending_reviews`.

    To compile this list, we need to retrieve information
    about each of the blocks listed in `pending_reviews` from modulestore.

    However, it is not possible to load a block from modulestore using only its `block_id`.
    So instead, we fetch all Adaptive Content Blocks belonging to `course`,
    and create a revision for each child of an ACB that has a pending review
    (i.e., each child whose `block_id` is listed in `pending_reviews`).
    """

    def usage_key_filter(usage_key):
        """
        Return True if `block_id` of `usage_key` is listed in `pending_reviews`,
        else False.
        """
        return usage_key.block_id in pending_reviews

    revisions = []
    adaptive_content_blocks = _get_adaptive_content_blocks(course)
    for adaptive_content_block in adaptive_content_blocks:
        relevant_children = adaptive_content_block.get_children(usage_key_filter=usage_key_filter)
        for child in relevant_children:
            revision = _get_revision(child, pending_reviews)
            revisions.append(revision)
    return revisions


def _get_adaptive_content_blocks(course):
    """
    Return list of Adaptive Content Blocks belonging to `course`.
    """
    course_key = course.location.course_key
    return modulestore().get_items(course_key, qualifiers={'category': 'adaptive_library_content'})


def _get_revision(child, due_dates):
    """
    Return revision containing URL, name, and due date for `child`.
    """
    usage_key = child.location
    url = get_redirect_url(usage_key.course_key, usage_key)
    name = child.display_name
    due_date = _make_timestamp(due_dates[usage_key.block_id])

    return {
        'url': url,
        'name': name,
        'due_date': due_date,
    }


def _make_timestamp(date_string):
    """
    Turn `date_string` into a Unix timestamp and return it.
    """
    return calendar.timegm(parser.parse(date_string).timetuple())
