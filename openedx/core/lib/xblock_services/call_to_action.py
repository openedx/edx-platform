"""
A module containing the CallToActionService which can be used for an xblock Runtime to supply
specific CTAs for specific XBlock contexts.
"""

from edx_django_utils.plugins import PluginManager


class CallToActionService(PluginManager):
    """
    An XBlock service that returns information on how to shift a learner's schedule.
    """
    NAMESPACE = 'openedx.call_to_action'

    def get_ctas(self, xblock, category):
        """
        Return the calls to action associated with the specified category for the given xblock.

        See the CallToActionService class constants for a list of recognized categories.

        Returns: list of dictionaries, describing the calls to action, with the following keys:
                 link, link_name, form_values, and description.
                 If the category is not recognized, an empty list is returned.

        An example of a returned list:
        [{
            'link': 'localhost:18000/skip',  # A link to POST to when the Call To Action is taken
            'link_name': 'Skip this Problem',  # The name of the action
            'form_values': {  # Any parameters to include with the CTA
                'foo': 'bar',
            },
            # A long-form description to be associated with the CTA
            'description': "If you don't want to do this problem, just skip it!",
            # A data set we include if the CTA is being rendered within an iframe. For example,
            # we do this in Learning MFE. This dictionary is passed to its's parent container via
            # parent.postMessage.  Parent containers should use window.onmessage event handler to
            # catch this dataset.
            'event_data': {
                'foo': 'bar',
            },
        }]

        Note: Future versions of this class may add a way to control the CTA method (POST vs GET),
        and would need to existing installed plugins to use the POST method.
        """
        ctas = []
        for cta_provider in self.get_available_plugins().values():
            ctas.extend(cta_provider().get_ctas(xblock, category))
        return ctas
