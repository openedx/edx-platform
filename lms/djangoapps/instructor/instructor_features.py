"""
Tabs for courseware.
"""
from openedx.core.lib.api.plugins import PluginManager


# Stevedore extension point namespaces
INSTRUCTOR_FEATURES_NAMESPACE = 'openedx.instructor_features'


class InstructorFeature(object):
    """
    A plugin that provides a new feature for the instructor dashboard.
    """

    # The type of the feature. This is primarily used as a unique identifier.
    type = ''

    # The category of the feature.
    category = 'miscellaneous'

    # The title of the feature, which should be internationalized using
    # ugettext_noop since the user won't be available in this context.
    title = None

    # A short description of the feature.
    description = None

    # The relative priority of this view that affects the ordering (lower numbers shown first)
    priority = None

    # The Font Awesome icon class to represent the feature
    icon_class = 'gear'

    # The name of the component to show for this feature
    component_name = None


class InstructorFeaturesPluginManager(PluginManager):
    """
    Manager for all of the instructor features that have been made available.

    All instructor tabs should be subclasses of InstructorFeature.
    """
    NAMESPACE = INSTRUCTOR_FEATURES_NAMESPACE

    @classmethod
    def get_instructor_features(cls):
        """
        Returns the list of available course tabs in their canonical order.
        """
        def compare_tabs(first_feature, second_feature):
            """
            Compares two instructor features, for use in sorting.

            This orders features by priority (when specified), and then
            alphabetically by title for features that are unprioritized.
            """
            first_priority = first_feature.priority
            second_priority = second_feature.priority
            if first_priority != second_priority:
                if first_priority is None:
                    return 1
                elif second_priority is None:
                    return -1
                else:
                    return first_priority - second_priority
            first_title = first_feature.title
            second_title = second_feature.title
            if first_title < second_title:
                return -1
            elif first_title == second_title:
                return 0
            else:
                return 1
        tab_types = cls.get_available_plugins().values()
        tab_types.sort(cmp=compare_tabs)
        return tab_types
