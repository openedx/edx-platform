import json
import logging

from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.capa_module import CapaModule, CapaDescriptor

log = logging.getLogger(__name__)


class CapaWikiModule(CapaModule):
    js = {'coffee': [resource_string(__name__, 'js/src/capa/display.coffee')],
          'js': [resource_string(__name__, 'js/src/capa/imageinput.js'),
                 resource_string(__name__, 'js/src/capa/schematic.js'),
                 resource_string(__name__, 'js/src/capawiki/peg-0.7.0.min.js')]}

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        # self._definition = {'capa': '<problem />', 'wiki': ''}
        self._definition = definition
        assert isinstance(definition['data'], dict) and 'capa' in definition['data']
        self.capa_definition = {'data': definition['data']['capa']}
        super(CapaWikiModule, self).__init__(system, location, self.capa_definition, instance_state,
                         shared_state, **kwargs)


class CapaWikiDescriptor(CapaDescriptor):
    js_module_name = "CapaWikiDescriptor"
    module_class = CapaWikiModule
    mako_template = "widgets/capawiki-edit.html"
