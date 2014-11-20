"""
TODO: something smart here
"""

from xblock.fields import XBlockMixin


class AuthoringMixin(XBlockMixin):
    """
    TODO:
    """
    @property
    def editor_tabs(self):
        return [
            {"display_name": "XML", "id": "xml"},
            {"display_name": "Settings", "id": "settings"}
        ]

    def save_editor(self, context=None):
        """
        TODO:
        """
        pass

    def settings_tab_view(self, context=None):
        """
        TODO:
        """
        pass

    def xml_tab_view(self, context=None):
        """
        TODO:
        """
        pass
