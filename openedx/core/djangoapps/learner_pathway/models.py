"""
Models for learner_pathway App.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

User = get_user_model()


class LearnerPathwayMembership(TimeStampedModel):
    """
    Model to store membership of learner in learner pathway
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pathway_uuid = models.UUIDField(help_text=_("UUID of associated pathway"))

    def __str__(self):
        """
        Create a human-readable string representation of the object.
        """
        return f'User: {self.user}, Pathway UUID: {self.pathway_uuid}'

    def __repr__(self):
        """
        Return string representation.
        """
        return f'<LearnerPathwayMembership user={self.user} pathway_uuid="{self.pathway_uuid}">'
