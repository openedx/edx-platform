""" AWS settings for zendesk proxy."""


def plugin_settings(settings):
    settings.ZENDESK_URL = settings.ENV_TOKENS.get('ZENDESK_URL', settings.ZENDESK_URL)
    settings.ZENDESK_OAUTH_ACCESS_TOKEN = settings.AUTH_TOKENS.get("ZENDESK_OAUTH_ACCESS_TOKEN")
