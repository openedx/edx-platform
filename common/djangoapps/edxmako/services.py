"""
Supports rendering an XBlock to HTML using mako templates.
"""

from xblock.reference.plugins import Service

from common.djangoapps.edxmako.shortcuts import render_to_string


class MakoService(Service):
    """
    A service for rendering XBlocks to HTML using mako templates.

    Args:
        namespace_prefix(string): optional prefix to the mako namespace used to find the template file.
           e.g to access LMS templates from within Studio code, pass namespace_prefix='lms.'
    """
    def __init__(
        self,
        namespace_prefix='',
        **kwargs
    ):
        super().__init__(**kwargs)
        self.namespace_prefix = namespace_prefix

    def render_template(self, template_file, dictionary, namespace='main'):
        """
        Takes (template_file, dictionary) and returns rendered HTML.
        """
        return render_to_string(template_file, dictionary, namespace=self.namespace_prefix + namespace)
