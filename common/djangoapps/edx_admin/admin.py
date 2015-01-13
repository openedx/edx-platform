"""
RatelimitSudoAdminSite
"""

from django.contrib.admin import *      # pylint: disable=wildcard-import, unused-wildcard-import
from django.contrib.admin import (site as django_site,
                                  autodiscover as django_autodiscover)
from ratelimitbackend.admin import RateLimitAdminSite
from sudo.admin import SudoAdminSite


class RatelimitSudoAdminSite(RateLimitAdminSite, SudoAdminSite):
    """
    A class that includes the features of both RateLimitAdminSite and SudoAdminSite
    """
    pass


site = RatelimitSudoAdminSite()     # pylint: disable=invalid-name


def autodiscover():     # pylint: disable=function-redefined
    """
    Auto-Discover admin models.
    """
    django_autodiscover()

    # pylint: disable=protected-access
    for model, modeladmin in django_site._registry.items():
        if model not in site._registry:
            site.register(model, modeladmin.__class__)
