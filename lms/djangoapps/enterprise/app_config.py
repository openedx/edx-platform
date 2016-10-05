from django.apps import AppConfig
from third_party_auth.auth_hooks import add_hook


class EnterpriseAppConfig(AppConfig):
    name = "enterprise"
    verbose_name = "Enterprise"

    def ready(self):
        add_hook("enterprise.hooks.sso_login_hook")
