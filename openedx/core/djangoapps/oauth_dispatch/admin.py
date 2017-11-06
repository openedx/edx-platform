from django.contrib import admin
from oauth2_provider.admin import ApplicationAdmin
from oauth2_provider.models import AccessToken, Grant, RefreshToken, get_application_model


def reregister(model_class):
    """
    Remove the existing admin, and register it anew with the given ModelAdmin

    Usage:

        @reregister(ModelClass)
        class ModelClassAdmin(ModelAdmin):
            pass
    """

    def decorator(cls):
        admin.site.unregister(model_class)
        admin.site.register(model_class, cls)
        return cls

    return decorator


@reregister(AccessToken)
class DOTAccessTokenAdmin(admin.ModelAdmin):
    date_hierarchy = 'expires'
    list_display = ('token', 'user', 'application', 'expires')
    list_filter = ('application',)
    raw_id_fields = ('user',)
    search_fields = ('token', 'user__username')


@reregister(RefreshToken)
class DOTRefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'application', 'access_token')
    list_filter = ('application',)
    raw_id_fields = ('user', 'access_token')
    search_fields = ('token', 'user__username', 'access_token__token')


@reregister(get_application_model())
class DOTApplicationAdmin(ApplicationAdmin):
    list_filter = ('client_type', 'authorization_grant_type', 'skip_authorization', 'restricted',)
    search_fields = ('name', 'user__username', 'client_id')


@reregister(Grant)
class DOTGrantAdmin(admin.ModelAdmin):
    date_hierarchy = 'expires'
    list_display = ('code', 'user', 'application', 'expires')
    list_filter = ('application',)
    raw_id_fields = ('user',)
    search_fields = ('code', 'user__username')
