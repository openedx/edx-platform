"""Production settings unique to the remote gradebook plugin."""


def plugin_settings(settings):
    """Settings for the remote gradebook plugin."""
    settings.REMOTE_GRADEBOOK = settings.ENV_TOKENS.get(
        "REMOTE_GRADEBOOK", settings.REMOTE_GRADEBOOK
    )
    settings.REMOTE_GRADEBOOK_USER = settings.AUTH_TOKENS.get(
        "REMOTE_GRADEBOOK_USER", settings.REMOTE_GRADEBOOK_USER
    )
    settings.REMOTE_GRADEBOOK_PASSWORD = settings.AUTH_TOKENS.get(
        "REMOTE_GRADEBOOK_PASSWORD", settings.REMOTE_GRADEBOOK_PASSWORD
    )
