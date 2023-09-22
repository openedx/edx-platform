"""
This module contains various configuration settings via
waffle switches for the Certificates app.
"""

from edx_toggles.toggles import SettingToggle, WaffleSwitch

# Namespace
WAFFLE_NAMESPACE = 'certificates'

# .. toggle_name: certificates.auto_certificate_generation
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: This toggle will enable certificates to be automatically generated
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2017-09-14
AUTO_CERTIFICATE_GENERATION = WaffleSwitch(f"{WAFFLE_NAMESPACE}.auto_certificate_generation", __name__)


# .. toggle_name: SEND_CERTIFICATE_CREATED_SIGNAL
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: When True, the system will publish `CERTIFICATE_CREATED` signals to the event bus. The
#   `CERTIFICATE_CREATED` signal is emit when a certificate has been awarded to a learner and the creation process has
#   completed.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-04-11
# .. toggle_target_removal_date: 2023-07-31
# .. toggle_tickets: TODO
SEND_CERTIFICATE_CREATED_SIGNAL = SettingToggle('SEND_CERTIFICATE_CREATED_SIGNAL', default=False, module_name=__name__)


# .. toggle_name: SEND_CERTIFICATE_REVOKED_SIGNAL
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: When True, the system will publish `CERTIFICATE_REVOKED` signals to the event bus. The
#   `CERTIFICATE_REVOKED` signal is emit when a certificate has been revoked from a learner and the revocation process
#   has completed.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-09-15
# .. toggle_target_removal_date: 2024-01-01
# .. toggle_tickets: TODO
SEND_CERTIFICATE_REVOKED_SIGNAL = SettingToggle('SEND_CERTIFICATE_REVOKED_SIGNAL', default=False, module_name=__name__)
