"""
This module contains various configuration settings via
waffle switches for the Certificates app.
"""


from edx_toggles.toggles import LegacyWaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = 'certificates'

# Switches
# TODO: Replace with WaffleSwitch(). See waffle() docstring.
AUTO_CERTIFICATE_GENERATION = 'auto_certificate_generation'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Certificates.

    IMPORTANT: Do NOT copy this pattern and do NOT use this to reference new switches.
      Instead, replace the string constant above with the actual switch instance.
      For example::

        AUTO_CERTIFICATE_GENERATION = WaffleSwitch(f'{WAFFLE_NAMESPACE}.auto_certificate_generation')
    """
    return LegacyWaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='Certificates: ')
