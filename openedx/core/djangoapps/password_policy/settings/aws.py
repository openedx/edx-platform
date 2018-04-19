def plugin_settings(settings):
    # Settings for managing the rollout of password policy compliance enforcement.
    config = dict(settings.ENV_TOKENS.get(
        'PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG',
        settings.PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG
    ))

    settings.PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG = config
