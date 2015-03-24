from .x_module import XModuleDescriptor, DescriptorSystem
from xblock.fragment import Fragment


class MakoDescriptorSystem(DescriptorSystem):
    def __init__(self, render_template, **kwargs):
        super(MakoDescriptorSystem, self).__init__(**kwargs)

        self.render_template = render_template


class MakoTemplateBlock(object):
    """
    Module descriptor intended as a mixin that uses a mako template
    to specify the module html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template

    MakoTemplateBlock.__init__ takes the same arguments as xmodule.x_module:XModuleDescriptor.__init__
    """

    def __init__(self, *args, **kwargs):
        super(MakoTemplateBlock, self).__init__(*args, **kwargs)
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

    def studio_view(self, context):
        import pudb; pu.db
        return Fragment(
            self.system.render_template(self.mako_template, self.get_context())
        )


class MakoModuleDescriptor(MakoTemplateBlock, XModuleDescriptor):
    def get_html(self):
        return self.studio_view(None).content
