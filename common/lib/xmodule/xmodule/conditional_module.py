import json
import logging

from xmodule.x_module import XModule
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor

from pkg_resources import resource_string

log = logging.getLogger('mitx.' + __name__)

class ConditionalModule(XModule):
    '''
    Blocks child module from showing unless certain conditions are met.

    Example:
        
        <conditional condition="require_completed" required="tag/url_name1&tag/url_name2">
            <video url_name="secret_video" />
        </conditional>

        <conditional condition="require_attempted" required="tag/url_name1&tag/url_name2">
            <video url_name="secret_video" />
        </conditional>

    '''

    js = {'coffee': [resource_string(__name__, 'js/src/conditional/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/javascript_loader.coffee'),
                    ]}

    js_module_name = "Conditional"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}


    def __init__(self, system, location, definition, descriptor, instance_state=None, shared_state=None, **kwargs):
        """
        In addition to the normal XModule init, provide:
        
            self.condition            = string describing condition required

        """
        XModule.__init__(self, system, location, definition, descriptor, instance_state, shared_state, **kwargs)
        self.contents = None
        self.condition = self.metadata.get('condition','')
        #log.debug('conditional module required=%s' % self.required_modules_list)

    def _get_required_modules(self):
        self.required_modules = []
        for descriptor in self.descriptor.get_required_module_descriptors():
            module = self.system.get_module(descriptor)
            self.required_modules.append(module)
        #log.debug('required_modules=%s' % (self.required_modules))

    def is_condition_satisfied(self):
        self._get_required_modules()

        if self.condition=='require_completed':
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
        elif self.condition=='require_attempted':
            # all required modules must be attempted, as determined by
            # the modules .is_attempted() method
            for module in self.required_modules:
                if not hasattr(module, 'is_attempted'):
                    raise Exception('Error in conditional module: required module %s has no .is_attempted() method' % module)
                if not module.is_attempted():
                    log.debug('conditional module: %s not attempted' % module)
                    return False
                else:
                    log.debug('conditional module: %s IS attempted' % module)
            return True
        else:
            raise Exception('Error in conditional module: unknown condition "%s"' % self.condition)

        return True

    def get_html(self):
        self.is_condition_satisfied()
        return self.system.render_template('conditional_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
        })

    def handle_ajax(self, dispatch, post):
        '''
        This is called by courseware.module_render, to handle an AJAX call.
        '''
        #log.debug('conditional_module handle_ajax: dispatch=%s' % dispatch)

        if not self.is_condition_satisfied():
            context = {'module': self}
            html = self.system.render_template('conditional_module.html', context)
            return json.dumps({'html': html})

        if self.contents is None:
            self.contents = [child.get_html() for child in self.get_display_items()]

        # for now, just deal with one child
        html = self.contents[0]
        
        return json.dumps({'html': html})

class ConditionalDescriptor(SequenceDescriptor):
    module_class = ConditionalModule

    filename_extension = "xml"

    stores_state = True
    has_score = False

    def __init__(self, *args, **kwargs):
        super(ConditionalDescriptor, self).__init__(*args, **kwargs)

        required_module_list = [tuple(x.split('/',1)) for x in self.metadata.get('required','').split('&')]
        self.required_module_locations = []
        for (tag, name) in required_module_list:
            loc = self.location.dict()
            loc['category'] = tag
            loc['name'] = name
            self.required_module_locations.append(Location(loc))
        log.debug('ConditionalDescriptor required_module_locations=%s' % self.required_module_locations)
        
    def get_required_module_descriptors(self):
        """Returns a list of XModuleDescritpor instances upon which this module depends, but are
        not children of this module"""
        return [self.system.load_item(loc) for loc in self.required_module_locations]
    
