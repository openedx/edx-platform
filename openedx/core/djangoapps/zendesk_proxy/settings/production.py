""" AWS settings for zendesk proxy."""


def plugin_settings(settings):
    settings.ZENDESK_URL = settings.EDXAPP_CONFIG.get('ZENDESK_URL', settings.ZENDESK_URL)
    settings.ZENDESK_OAUTH_ACCESS_TOKEN = settings.EDXAPP_CONFIG.get("ZENDESK_OAUTH_ACCESS_TOKEN")
