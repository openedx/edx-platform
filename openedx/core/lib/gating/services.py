"""
A wrapper class to communicate with Gating api
"""

from . import api as gating_api


class GatingService:
    """
    An XBlock service to talk to the Gating api.
    """

    def compute_is_prereq_met(self, content_id, user_id, recalc_on_unmet=False):
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
        return gating_api.compute_is_prereq_met(content_id, user_id, recalc_on_unmet)

    def required_prereq(self, course_key, content_key, relationship):
        """
        Returns the prerequisite if one is required

        Arguments:
            course_key (str|CourseKey): The course key
            content_key (str|UsageKey): The content usage key
            relationship (str): The relationship type (e.g. 'requires')

        Returns:
            dict or None: The gating milestone dict or None
        """
        return gating_api.get_gating_milestone(course_key, content_key, relationship)

    def is_gate_fulfilled(self, course_key, gating_content_key, user_id):
        """
        Determines if a prerequisite section specified by gating_content_key
        has any unfulfilled milestones.

        Arguments:
            course_key (CourseUsageLocator): Course locator
            gating_content_key (BlockUsageLocator): The locator for the section content
            user_id: The id of the user

        Returns:
            Returns True if section has no unfufilled milestones or is not a prerequisite.
            Returns False otherwise
        """
        return gating_api.is_gate_fulfilled(course_key, gating_content_key, user_id)
