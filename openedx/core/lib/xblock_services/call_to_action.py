from openedx.core.lib.plugins import PluginManager


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
            'link': 'localhost:18000/skip',
            'link_name': 'Skip this Problem',
            'form_values': {
                'foo': 'bar',
            },
            'description': "If you don't want to do this problem, just skip it!"
        }]
        """
        ctas = []
        for cta_provider in self.get_available_plugins().values():
            ctas.extend(cta_provider().get_ctas(xblock, category))
        return ctas
