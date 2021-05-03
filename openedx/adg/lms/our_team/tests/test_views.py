"""
Tests for all the views in our team app
"""
import pytest
from django.test import RequestFactory
from django.urls import reverse

from openedx.adg.lms.our_team.models import OurTeamMember
from openedx.adg.lms.our_team.views import OurTeamView

from .factories import OurTeamMemberFactory


@pytest.mark.django_db
def test_our_team_view():
    """
    Test if the our_team view is working with the correct context
    """
    OurTeamMemberFactory(member_type=OurTeamMember.TEAM_MEMBER)
    OurTeamMemberFactory(member_type=OurTeamMember.BOARD_MEMBER)

    our_team_get_request = RequestFactory().get(reverse('our_team'))
    response = OurTeamView.as_view()(our_team_get_request)

    expected_team_members = OurTeamMember.objects.team_members()
    actual_team_members = response.context_data.get('team_members')

    expected_board_of_trustees = OurTeamMember.objects.board_of_trustees()
    actual_board_of_trustees = response.context_data.get('board_of_trustees')

    assert response.status_code == 200
    assert set(actual_team_members) == set(expected_team_members)
    assert set(actual_board_of_trustees) == set(expected_board_of_trustees)
