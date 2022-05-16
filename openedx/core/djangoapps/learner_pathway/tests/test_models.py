"""
tests for learner_pathway models
"""

from django.test import TestCase

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.learner_pathway.tests.factories import LearnerPathwayMembershipFactory


class LearnerPathwayMembershipTests(TestCase):
    """
    LearnerPathwayMembership model tests
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_string_representation(self):
        """
        Test the string representation of the LearnerPathwayMembership model.
        """
        membership = LearnerPathwayMembershipFactory(user=self.user)
        expected_str = f'User: {membership.user}, Pathway UUID: {membership.pathway_uuid}'
        expected_repr = f'<LearnerPathwayMembership user={membership.user} pathway_uuid="{membership.pathway_uuid}">'
        assert expected_str == str(membership)
        assert expected_repr == repr(membership)
