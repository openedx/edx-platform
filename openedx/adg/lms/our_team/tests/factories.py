"""
Factories for our_team app
"""
import factory

from openedx.adg.lms.our_team.models import OurTeamMember


class OurTeamMemberFactory(factory.DjangoModelFactory):
    """
    Factory for OurTeamMember model
    """

    class Meta:
        model = OurTeamMember
