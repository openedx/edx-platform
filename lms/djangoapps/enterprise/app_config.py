"""
Application config for enterpirse app
"""
from django.apps import AppConfig
from third_party_auth.auth_hooks import add_hook as add_third_party_auth_hook


class EnterpriseAppConfig(AppConfig):
    name = "enterprise"
    verbose_name = "Enterprise"

    def ready(self):
        # registers sso_login_hook method with third party auth pipeline
        add_third_party_auth_hook("enterprise.hooks.sso_login_hook")
