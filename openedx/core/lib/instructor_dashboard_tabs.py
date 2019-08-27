"""
Tabs for the instructor dashboard.
"""
from __future__ import absolute_import

from openedx.core.lib.plugins import PluginManager


# Stevedore extension point namespaces
INSTRUCTOR_DASHBOARD_TAB_NAMESPACE = 'lms.instructor_dashboard.tab'


class InstructorDashboardTabPluginManager(PluginManager):
    """
    Manager for all of the course tabs that have been made available.

    TODO: develop abstract base class for tabs to implement.
    """
    NAMESPACE = INSTRUCTOR_DASHBOARD_TAB_NAMESPACE

    @classmethod
    def get_tabs(cls):
        """
        Returns the list of available tabs in their canonical order.
        """
        tabs = list(cls.get_available_plugins().values())
        tabs.sort(key=lambda tab: (tab.priority, tab.section_key))
        return tabs
