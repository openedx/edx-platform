import json
import logging
from xmodule.x_module import XModule
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor
from xblock.core import List, String, Scope, Integer
from lxml import etree
from pkg_resources import resource_string

log = logging.getLogger('mitx.' + __name__)

class ConditionalModule(XModule):
    '''
    Blocks child module from showing unless certain conditions are met.

    Example:

        <conditional condition="require_completed" required="tag/url_name1&tag/url_name2">
            <video url_name="secret_video" />
        </conditional>

    '''

    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/conditional/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),

                    ]}

    js_module_name = "Conditional"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    # xml_object = String(scope=Scope.content)
    contents = String(scope=Scope.content)
    show_modules = String(scope=Scope.content)

    def _get_required_modules(self):
        self.required_modules = []
        for loc in self.descriptor.required_module_locations:
            module = self.system.get_module(loc)
            self.required_modules.append(module)
        #log.debug('required_modules=%s' % (self.required_modules))

    def _get_condition(self):
        return self.descriptor.xml_attributes.get('condition', '')

    def is_condition_satisfied(self):
        self._get_required_modules()
        self.condition = self._get_condition()

        if self.condition == 'require_completed':
            # all required modules must be completed, as determined by
            # the modules .is_completed() method
            for module in self.required_modules:
                #log.debug('in is_condition_satisfied; student_answers=%s' % module.lcp.student_answers)
                #log.debug('in is_condition_satisfied; instance_state=%s' % module.instance_state)
                if not hasattr(module, 'is_completed'):
                    raise Exception('Error in conditional module: required module %s has no .is_completed() method' % module)
                if not module.is_completed():
                    log.debug('conditional module: %s not completed' % module)
                    return False
                else:
                    log.debug('conditional module: %s IS completed' % module)
            return True
        elif self.condition == 'answer':
            for module in self.required_modules:
                if not hasattr(module, 'poll_answer'):
                    raise Exception('Error in conditional module: required module %s has no poll_answer field' % module)
                answer =  self.descriptor.xml_attributes.get('answer')
                if answer == 'unanswered' and module.poll_answer:
                    return False
                if module.poll_answer != answer:
                    return False
            return True
        else:
            raise Exception('Error in conditional module: unknown condition "%s"' % self.condition)

        return False

    def get_html(self):
        # self.is_condition_satisfied()
        return self.system.render_template('conditional_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
        })

    def _get_modules_to_show(self):
        to_show = [tuple(x.strip().split('/',1)) for x in self.show_modules.split(';')]
        self.modules_to_show = []
        for (tag, name) in to_show:
            loc = self.location.dict()
            loc['category'] = tag
            loc['name'] = name
            self.modules_to_show.append(Location(loc))


    def handle_ajax(self, dispatch, post):
        '''
        This is called by courseware.moduleodule_render, to handle an AJAX call.
        '''
        # import ipdb; ipdb.set_trace()
        #log.debug('conditional_module handle_ajax: dispatch=%s' % dispatch)
        if not self.is_condition_satisfied():
            context = {'module': self}
            html = self.system.render_template('conditional_module.html', context)
            return json.dumps({'html': [html]})

        if self.contents is None:
            import ipdb; ipdb.set_trace()
            # self.contents = [child.get_html() for child in self.get_display_items()]
            self.contents = [self.system.get_module(x).get_html() for x in self.modules_to_show]
            self.contents += [self.system.get_module(child_descriptor.location).get_html()
                    for child_descriptor in self.descriptor.get_children()]


        html = self.contents
        #log.debug('rendered conditional module %s' % str(self.location))
        return json.dumps({'html': html})

class ConditionalDescriptor(SequenceDescriptor):
    ''' TODO check exports'''
    module_class = ConditionalModule

    filename_extension = "xml"

    stores_state = True
    has_score = False

    show_modules = String(scope=Scope.content)

    def __init__(self, *args, **kwargs):
        super(ConditionalDescriptor, self).__init__(*args, **kwargs)
        # import ipdb; ipdb.set_trace()
        required_module_list = [(x.strip().split('/',5)[4:6]) for x in self.xml_attributes.get('source','').split(';')]
        self.required_module_locations = []
        for (tag, name) in required_module_list:
            loc = self.location.dict()
            loc['category'] = tag
            loc['name'] = name
            self.required_module_locations.append(Location(loc))
        # import ipdb; ipdb.set_trace()
        log.debug('ConditionalDescriptor required_module_locations=%s' % self.required_module_locations)

    def get_required_module_descriptors(self):
        """Returns a list of XModuleDescritpor instances upon which this module depends, but are
        not children of this module"""
        return [self.system.load_item(loc) for loc in self.required_module_locations]

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            if child.tag != 'show':
                try:
                    children.append(system.process_xml(etree.tostring(child)).location.url())
                except Exception, e:
                    log.exception("Unable to load child when parsing Conditional. Continuing...")
                    if system.error_tracker is not None:
                        system.error_tracker("ERROR: " + str(e))
                    continue
            else:
                cls.show_modules = child.get('source')
        return {'show_modules':''}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('sequential')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object
