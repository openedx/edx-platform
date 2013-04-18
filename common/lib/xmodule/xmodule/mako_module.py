from .x_module import XModuleDescriptor, DescriptorSystem
from .modulestore.inheritance import own_metadata
from xblock.core import Scope



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
            'editable_metadata_fields': self.editable_metadata_fields,
        }

    def get_html(self):
        return self.system.render_template(
            self.mako_template, self.get_context())

    # cdodge: encapsulate a means to expose "editable" metadata fields (i.e. not internal system metadata)
    @property
    def editable_metadata_fields(self):
#        fields = {}
#        for field, value in own_metadata(self).items():
#            if field in self.system_metadata_fields:
#                continue
#
#            fields[field] = value
#        return fields
        inherited_metadata = getattr(self, '_inherited_metadata', {})
        metadata = {}
        for field in self.fields:
            # Only save metadata that wasn't inherited
            if field.scope != Scope.settings or field.name in self.system_metadata_fields:
                continue

            if field.name in self._model_data:
                metadata[field.name] = self._model_data[field.name]
                if field.name in inherited_metadata and self._model_data.get(field.name) == inherited_metadata.get(
                    field.name):
                    metadata[field.name] = str(metadata[field.name]) + ' INHERITED'
            else:
                metadata[field.name] = str(getattr(self, field.name)) + ' DEFAULT'

        return metadata
