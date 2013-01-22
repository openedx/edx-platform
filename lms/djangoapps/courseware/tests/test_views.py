from unittest import TestCase
import logging
from mock import MagicMock, patch

from django.conf import settings
from django.test.utils import override_settings

import courseware.views as views

class Stub():
    pass

class ViewsTestCase(TestCase):
    def setUp(self):
        pass


    def test_user_groups(self):
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertEquals(views.user_groups(mock_user),[])

    @override_settings(DEBUG = True)
    def test_user_groups_debug(self):
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = True
        pass
        #views.user_groups(mock_user)
        #Keep going later

    def test_get_current_child(self):
        self.assertIsNone(views.get_current_child(Stub()))
        mock_xmodule = MagicMock()
        mock_xmodule.position = -1
        mock_xmodule.get_display_items.return_value = ['one','two']
        print views.user_groups(mock_xmodule)
        self.assertEquals(views.user_groups(mock_xmodule), 'one')
