"""
This module contains various configuration settings via waffle switches for the Credentials app.
"""

from edx_toggles.toggles import WaffleSwitch

# Namespace
WAFFLE_NAMESPACE = 'credentials'

# .. toggle_name: credentials.use_learner_record_mfe
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: This toggle will inform the Program Dashboard to route to the Learner Record MFE over the
#     legacy frontend of the Credentials IDA.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2022-09-07
USE_LEARNER_RECORD_MFE = WaffleSwitch(f"{WAFFLE_NAMESPACE}.use_learner_record_mfe", __name__)
