"""Utilities to assist with oauth scopes enforcement"""
from waffle import switch_is_active


def is_oauth_scope_enforcement_enabled():
    """
    Returns True if switch is enabled
    """
    return switch_is_active('ENABLE_OAUTH_SCOPE_ENFORCEMENT')

