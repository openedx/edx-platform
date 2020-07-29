import mock

from lms.djangoapps.homepage.constants import CONFIGS
from lms.djangoapps.homepage.custom_context_processors import notifications_configs


@mock.patch('lms.djangoapps.homepage.custom_context_processors.get_notifications_widget_context')
def test_notifications_configs(mock_get_notifications_widget_context):
    mock_get_notifications_widget_context.return_value = 'data'
    data = notifications_configs('request')
    mock_get_notifications_widget_context.assert_called_once_with(CONFIGS)
    assert data == 'data'
