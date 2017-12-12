"""
A wrapper class to communicate with Gating api
"""
from . import api as gating_api


class GatingService(object):
    """
    An XBlock service to talk to the Gating api.
    """

    def is_prereq_met(self, content_id, user_id, recalc_on_unmet=False):
        """
        Returns true if the prequiste has been met for a given milestone

        Arguments:
            content_id (BlockUsageLocator): BlockUsageLocator for the content
            user_id: The id of the user
            recalc_on_unmet: Recalculate the grade if prereq has not yet been met

        Returns:
            tuple: True|False,
            prereq_meta_info = { 'url': prereq_url|None, 'display_name': prereq_name|None}
        """       
        return gating_api.is_prereq_met(content_id, user_id, recalc_on_unmet)

    def is_prereq_required(self, course_key, content_key, relationship):
        """
        Returns the prerequiste if one is required

        Arguments:
            course_key (str|CourseKey): The course key
            content_key (str|UsageKey): The content usage key
            relationship (str): The relationship type (e.g. 'requires')

        Returns:
            dict or None: The gating milestone dict or None
        """
        return gating_api.get_gating_milestone(course_key, content_key, relationship)
