"""
The ccxcon app contains the models and the APIs to  interact
with the `CCX Connector`, an application external to openedx
that is used to interact with the CCX and their master courses.

The ccxcon app needs to be placed in `openedx.core.djangoapps`
because it will be used both in CMS and LMS.
"""
import openedx.core.djangoapps.ccxcon.signals
