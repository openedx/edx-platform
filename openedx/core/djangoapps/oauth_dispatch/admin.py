"""
Override admin configuration for django-oauth-toolkit
"""


from django.contrib.admin import ModelAdmin, site
from oauth2_provider import models

from .models import ApplicationAccess, RestrictedApplication


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
    date_hierarchy = 'expires'
    list_display = ['token', 'user', 'application', 'expires']
    list_filter = ['application']
    raw_id_fields = ['user']
    search_fields = ['token', 'user__username']


@reregister(models.RefreshToken)
class DOTRefreshTokenAdmin(ModelAdmin):
    """
    Custom AccessToken Admin
    """
    list_display = ['token', 'user', 'application', 'access_token']
    list_filter = ['application']
    raw_id_fields = ['user', 'access_token']
    search_fields = ['token', 'user__username', 'access_token__token']


@reregister(models.Grant)
class DOTGrantAdmin(ModelAdmin):
    """
    Custom Grant Admin
    """
    date_hierarchy = 'expires'
    list_display = ['code', 'user', 'application', 'expires']
    list_filter = ['application']
    raw_id_fields = ['user']
    search_fields = ['code', 'user__username']


@reregister(models.get_application_model())
class DOTApplicationAdmin(ModelAdmin):
    """
    Custom Application Admin
    """
    list_display = ['name', 'user', 'client_type', 'authorization_grant_type', 'client_id']
    list_filter = ['client_type', 'authorization_grant_type', 'skip_authorization']
    raw_id_fields = ['user']
    search_fields = ['name', 'user__username', 'client_id']


class ApplicationAccessAdmin(ModelAdmin):
    """
    ModelAdmin for ApplicationAccess
    """
    list_display = ['application', 'scopes', 'filters']


class RestrictedApplicationAdmin(ModelAdmin):
    """
    ModelAdmin for the Restricted Application
    """
    list_display = ['application']


site.register(ApplicationAccess, ApplicationAccessAdmin)
site.register(RestrictedApplication, RestrictedApplicationAdmin)
