from x_module import XModuleDescriptor
from mitxmako.shortcuts import render_to_string


class MakoModuleDescriptor(XModuleDescriptor):
    """
    Module descriptor intended as a mixin that uses a mako template
    to specify the module html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template
    """

    def get_context(self):
        """
        Return the context to render the mako template with
        """
        return {'module': self}

    def get_html(self):
        return render_to_string(self.mako_template, self.get_context())
