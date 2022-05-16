"""
Learner pathway factories
"""

from uuid import uuid4

from factory.django import DjangoModelFactory

from openedx.core.djangoapps.learner_pathway.models import LearnerPathwayMembership


class LearnerPathwayMembershipFactory(DjangoModelFactory):
    """
    LearnerPathwayMembership factory
    """
    class Meta:
        model = LearnerPathwayMembership

    pathway_uuid = uuid4()
