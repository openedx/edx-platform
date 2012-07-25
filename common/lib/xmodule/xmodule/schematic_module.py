import json

from x_module import XModule, XModuleDescriptor


class ModuleDescriptor(XModuleDescriptor):
    pass


class Module(XModule):
    def get_html(self):
        return '<input type="hidden" class="schematic" name="{item_id}" height="480" width="640">'.format(item_id=self.item_id)
