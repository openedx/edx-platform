"""
patching helpers
"""

from mock import Mock


# Keep Signal receivers in tahoe_idp from executing fully when not explicitly testing
dummy_receivers_idp_not_enabled = Mock()
dummy_receivers_idp_not_enabled.return_value = False
