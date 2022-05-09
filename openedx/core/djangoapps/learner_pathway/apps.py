"""
Configuration for learner_pathway Django app
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LearnerPathwayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learner_pathway'
    verbose_name = _("Learner Pathways")
