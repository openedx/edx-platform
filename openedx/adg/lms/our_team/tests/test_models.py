"""
All the tests for models.py of our_team app
"""
import factory
import pytest

from openedx.adg.lms.our_team.models import OurTeamMember

from .factories import OurTeamMemberFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    'member_types, expected_team_members, expected_trustees', [
        ([], 0, 0),
        ([OurTeamMember.TEAM_MEMBER], 1, 0),
        ([OurTeamMember.BOARD_MEMBER], 0, 1),
        ([OurTeamMember.TEAM_MEMBER, OurTeamMember.BOARD_MEMBER], 1, 1),
        ([OurTeamMember.TEAM_MEMBER, OurTeamMember.TEAM_MEMBER, OurTeamMember.BOARD_MEMBER], 2, 1)
    ]
)
def test_our_team_members_managers(member_types, expected_team_members, expected_trustees):
    """
    Test if the manager for OurTeamMember model works correctly in all cases
    """
    members = factory.Iterator(member_types)
    OurTeamMemberFactory.create_batch(len(member_types), member_type=members)

    assert OurTeamMember.objects.team_members().count() == expected_team_members
    assert OurTeamMember.objects.board_of_trustees().count() == expected_trustees
    assert OurTeamMember.objects.count() == expected_team_members + expected_trustees
