"""
Code to handle mako templating for XModules and XBlocks.
"""
from xblock.fragment import Fragment

from .x_module import XModuleDescriptor, DescriptorSystem, shim_xmodule_js


class MakoDescriptorSystem(DescriptorSystem):
    def __init__(self, render_template, **kwargs):
        super(MakoDescriptorSystem, self).__init__(**kwargs)

        self.render_template = render_template


class MakoTemplateBlockBase(object):
    """
    XBlock intended as a mixin that uses a mako template
    to specify the module html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template
    """
    # pylint: disable=no-member

    def __init__(self, *args, **kwargs):
        super(MakoTemplateBlockBase, self).__init__(*args, **kwargs)
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
        shim_xmodule_js(self, fragment)
        return fragment


class MakoModuleDescriptor(MakoTemplateBlockBase, XModuleDescriptor):  # pylint: disable=abstract-method
    """
    Mixin to use for XModule descriptors.
    """
    def get_html(self):
        return self.studio_view(None).content
