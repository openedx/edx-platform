from x_module import XModuleDescriptor, DescriptorSystem


class MakoDescriptorSystem(DescriptorSystem):
    def __init__(self, load_item, resources_fs, error_tracker,
                 render_template, **kwargs):
        super(MakoDescriptorSystem, self).__init__(
            load_item, resources_fs, error_tracker, **kwargs)

        self.render_template = render_template


class MakoModuleDescriptor(XModuleDescriptor):
    """
    Module descriptor intended as a mixin that uses a mako template
    to specify the module html.

    Expects the descriptor to have the `mako_template` attribute set
    with the name of the template to render, and it will pass
    the descriptor as the `module` parameter to that template
    """

    def __init__(self, system, definition=None, **kwargs):
        if getattr(system, 'render_template', None) is None:
            raise TypeError('{system} must have a render_template function'
                            ' in order to use a MakoDescriptor'.format(
                    system=system))
        super(MakoModuleDescriptor, self).__init__(system, definition, **kwargs)

    def get_context(self):
        """
        Return the context to render the mako template with
        """
        return {'module': self,
                'metadata': self.metadata
                }

    def get_html(self):
        return self.system.render_template(
            self.mako_template, self.get_context())
