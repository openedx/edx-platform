"""
Override admin configuration for django-oauth-toolkit
"""

from django.contrib.admin import ModelAdmin, site
from oauth2_provider import models

from .models import RestrictedApplication, ScopedApplicationOrganization


def reregister(model_class):
    """
    Remove the existing admin, and register it anew with the given ModelAdmin

    Usage:

        @reregister(ModelClass)
        class ModelClassAdmin(ModelAdmin):
            pass
    """
    def decorator(cls):
        """
        The actual decorator that does the work.
        """
        site.unregister(model_class)
        site.register(model_class, cls)
        return cls

    return decorator


@reregister(models.AccessToken)
class DOTAccessTokenAdmin(ModelAdmin):
    """
    Custom AccessToken Admin
    """
    date_hierarchy = u'expires'
    list_display = [u'token', u'user', u'application', u'expires']
    list_filter = [u'application']
    raw_id_fields = [u'user']
    search_fields = [u'token', u'user__username']


@reregister(models.RefreshToken)
class DOTRefreshTokenAdmin(ModelAdmin):
    """
    Custom AccessToken Admin
    """
    list_display = [u'token', u'user', u'application', u'access_token']
    list_filter = [u'application']
    raw_id_fields = [u'user', u'access_token']
    search_fields = [u'token', u'user__username', u'access_token__token']


@reregister(models.Grant)
class DOTGrantAdmin(ModelAdmin):
    """
    Custom Grant Admin
    """
    date_hierarchy = u'expires'
    list_display = [u'code', u'user', u'application', u'expires']
    list_filter = [u'application']
    raw_id_fields = [u'user']
    search_fields = [u'code', u'user__username']


class RestrictedApplicationAdmin(ModelAdmin):
    """
    ModelAdmin for the Restricted Application
    """
    list_display = [u'application']


site.register(RestrictedApplication, RestrictedApplicationAdmin)


class ScopedApplicationOrganizationAdmin(ModelAdmin):
    """
    ModelAdmin for the ScopedApplicationOrganization model.
    """
    list_display = [u'application', 'short_name', 'provider_type']


site.register(ScopedApplicationOrganization, ScopedApplicationOrganizationAdmin)
