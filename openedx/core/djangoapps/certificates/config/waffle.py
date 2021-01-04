"""
This module contains various configuration settings via
waffle switches for the Certificates app.
"""


from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'certificates'

# Switches
AUTO_CERTIFICATE_GENERATION = u'auto_certificate_generation'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Certificates.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Certificates: ')
