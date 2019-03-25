"""
Production settings for the password_policy app.
"""


def plugin_settings(settings):
    """
    Override the default password_policy app settings with production settings.
    """
    config = dict(settings.PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG)
    config.update(settings.ENV_TOKENS.get('PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG', {}))
    settings.PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG = config
