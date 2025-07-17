"""
Code to handle mako templating for XModules and XBlocks.
"""


from web_fragments.fragment import Fragment

from .x_module import DescriptorSystem, shim_xmodule_js


class MakoDescriptorSystem(DescriptorSystem):  # lint-amnesty, pylint: disable=abstract-method
    """
    Descriptor system that renders mako templates.
    """
    def __init__(self, render_template, **kwargs):
        super().__init__(**kwargs)

        self.render_template = render_template

        # Add the MakoService to the runtime services.
        # If it already exists, do not attempt to reinitialize it; otherwise, this could override the `namespace_prefix`
        # of the `MakoService`, breaking template rendering in Studio.
        #
        # This is not needed by most XBlocks, because the MakoService is added to their runtimes.
        # However, there are a few cases where the MakoService is not added to the XBlock's
        # runtime. Specifically:
        # * in the Instructor Dashboard bulk emails tab, when rendering the HtmlBlock for its WYSIWYG editor.
        # * during testing, when fetching factory-created blocks.
        if 'mako' not in self._services:
            from common.djangoapps.edxmako.services import MakoService
            self._services['mako'] = MakoService()


class MakoTemplateBlockBase:
    """
    XBlock intended as a mixin that uses a mako template
    to specify the block html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template
    """
    # pylint: disable=no-member

    js_module_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_context(self):
        """
        Return the context to render the mako template with
        """
        return {
            'module': self,
            'editable_metadata_fields': self.editable_metadata_fields
        }

    def studio_view(self, context):  # pylint: disable=unused-argument
        """
        View used in Studio.
        """
        # pylint: disable=no-member
        fragment = Fragment(
            self.runtime.service(self, 'mako').render_template(self.mako_template, self.get_context())
        )
        shim_xmodule_js(fragment, self.js_module_name)
        return fragment
