from .x_module import XModuleDescriptor, DescriptorSystem
from .fields import NonEditableSettingsScope
from xblock.core import Scope
from xblock.core import XBlock


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

    def __init__(self, system, location, model_data):
        if getattr(system, 'render_template', None) is None:
            raise TypeError('{system} must have a render_template function'
                            ' in order to use a MakoDescriptor'.format(
                    system=system))
        super(MakoModuleDescriptor, self).__init__(system, location, model_data)

    def get_context(self):
        """
        Return the context to render the mako template with
        """
        return {
            'module': self,
            'editable_metadata_fields': self.editable_metadata_fields
        }

    def get_html(self):
        return self.system.render_template(
            self.mako_template, self.get_context())

    @property
    def editable_metadata_fields(self):
        inherited_metadata = getattr(self, '_inherited_metadata', {})
        metadata = {}
        for field in self.fields:

            if field.scope != Scope.settings or isinstance(field.scope, NonEditableSettingsScope):
                continue

            # We are not allowing editing of xblock tag and name fields at this time (for any component).
            if field == XBlock.tags or field == XBlock.name:
                continue

            inherited = False
            default = False
            value = getattr(self, field.name)
            if field.name in self._model_data:
                default = False
                if field.name in inherited_metadata and self._model_data.get(field.name) == inherited_metadata.get(
                    field.name):
                    inherited = True
            else:
                default = True

            metadata[field.name] = {'field' : field,
                                    'value': value,
                                    'is_inherited': inherited,
                                    'is_default': default }

        return metadata
