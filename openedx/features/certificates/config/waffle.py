"""
This module contains various configuration settings via
waffle switches for the Certificates app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'certificates'

# Switches
AUTO_GENERATED_CERTIFICATES = u'auto_generated_certificates'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Certificates.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Certificates: ')


def auto_generated_certificates_enabled():
    return waffle().is_enabled(AUTO_GENERATED_CERTIFICATES)
