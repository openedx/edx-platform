"""
Code to handle mako templating for XModules and XBlocks.
"""


from web_fragments.fragment import Fragment
from xblock.core import XBlock

from .x_module import DescriptorSystem, shim_xmodule_js, XModuleMixin


class MakoDescriptorSystem(DescriptorSystem):  # lint-amnesty, pylint: disable=abstract-method
    """
    Descriptor system that renders mako templates.
    """
    def __init__(self, render_template, **kwargs):
        super().__init__(**kwargs)

        self.render_template = render_template

        # Add the MakoService to the descriptor system.
        #
        # This is not needed by most XBlocks, because they are initialized with a full runtime ModuleSystem that already
        # has the MakoService.
        # However, there are a few cases where the XBlock only has the descriptor system instead of the full module
        # runtime. Specifically:
        # * in the Instructor Dashboard bulk emails tab, when rendering the HtmlBlock for its WYSIWYG editor.
        # * during testing, when using the ModuleSystemTestCase to fetch factory-created blocks.
        from common.djangoapps.edxmako.services import MakoService
        self._services['mako'] = MakoService()


class MakoTemplateBlockBase:
    """
    XBlock intended as a mixin that uses a mako template
    to specify the module html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template
    """
    # pylint: disable=no-member

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self.runtime, 'render_template', None) is None:
            raise TypeError(
                '{runtime} must have a render_template function'
                ' in order to use a MakoDescriptor'.format(
                    runtime=self.runtime,
                )
            )

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
            self.system.render_template(self.mako_template, self.get_context())
        )
        shim_xmodule_js(fragment, self.js_module_name)
        return fragment


@XBlock.needs("i18n")
class MakoModuleDescriptor(MakoTemplateBlockBase, XModuleMixin):  # pylint: disable=abstract-method
    """
    Mixin to use for XModule descriptors.
    """
    resources_dir = None

    def get_html(self):
        return self.studio_view(None).content
