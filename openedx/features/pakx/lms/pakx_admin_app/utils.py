"""
helpers functions for Admin Panel API
"""
from django.db.models.query_utils import Q
from organizations.models import Organization

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS


def get_user_org_filter(user):
    organization = Organization.objects.get(user_profiles__user=user)
    return {'profile__organization': organization}


def get_learners_filter():
    return Q(
        Q(is_superuser=False) & Q(is_staff=False) &
        ~Q(groups__name__in=[GROUP_TRAINING_MANAGERS, GROUP_ORGANIZATION_ADMIN])
    )
