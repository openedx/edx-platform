"""
Toggles for accounts related code.
"""
from openedx.core.djangoapps.waffle_utils import WaffleFlag


# .. toggle_name: REDIRECT_TO_ORDER_HISTORY_MICROFRONTEND
# .. toggle_type: waffle_flag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of a new micro-frontend-based implementation of the order history page.
# .. toggle_category: micro-frontend
# .. toggle_use_cases: incremental_release, open_edx
# .. toggle_creation_date: 2019-04-11
# .. toggle_expiration_date: 2020-12-31
# .. toggle_warnings: Remember to also set ORDER_HISTORY_MICROFRONTEND_URL before this toggle is enabled.
# .. toggle_tickets: DEPR-17
# .. toggle_status: supported
REDIRECT_TO_ORDER_HISTORY_MICROFRONTEND = WaffleFlag('order_history', 'redirect_to_microfrontend')
