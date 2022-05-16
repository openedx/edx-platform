"""
Admin interface for learner_pathway App.
"""
from django.contrib import admin

from openedx.core.djangoapps.learner_pathway.models import LearnerPathwayMembership


class LearnerPathwayMembershipAdmin(admin.ModelAdmin):
    """
    Admin for LearnerPathwayMembership Model
    """
    raw_id_fields = ("user", )
    list_display = ('user', 'pathway_uuid', 'created')

    class Meta:
        model = LearnerPathwayMembership


admin.site.register(LearnerPathwayMembership, LearnerPathwayMembershipAdmin)
