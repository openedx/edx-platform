"""
This module contains various configuration settings via
waffle switches for the Certificates app.
"""

from edx_toggles.toggles import WaffleSwitch

# Namespace
WAFFLE_NAMESPACE = 'certificates'

AUTO_CERTIFICATE_GENERATION = WaffleSwitch(f"{WAFFLE_NAMESPACE}.auto_certificate_generation", __name__)
