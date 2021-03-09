"""
This module contains various configuration settings via
waffle switches for the Certificates app.
"""


from edx_toggles.toggles import WaffleSwitch


# Switches
# .. toggle_name: certificates.auto_certificate_generation
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, certificates are generated automatically
#   when learners reach the pass grade (self-paced courses) or available date
#   (instructor-led courses).
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2017-05-09
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/15937
AUTO_CERTIFICATE_GENERATION = WaffleSwitch(
    "certificates.auto_certificate_generation", __name__
)
