import json
import logging

from lxml import etree

from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.progress import Progress

log = logging.getLogger("mitx.common.lib.seq_module")

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class SequenceModule(XModule):
    ''' Layout module which lays out content in a temporal sequence
    '''
    def get_instance_state(self):
        return json.dumps({'position': self.position})

    def get_html(self):
        self.render()
        return self.content

    def get_progress(self):
        ''' Return the total progress, adding total done and total available.
        (assumes that each submodule uses the same "units" for progress.)
        '''
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses)
        return progress

    def handle_ajax(self, dispatch, get):		# TODO: bounds checking
        ''' get = request.POST instance '''
        if dispatch=='goto_position':
            self.position = int(get['position'])
            return json.dumps({'success':True})
        raise self.system.exception404

    def render(self):
        if self.rendered:
            return
        ## Returns a set of all types of all sub-children
        contents = []
        for child in self.get_display_items():
            progress = child.get_progress()
            contents.append({
                'content': child.get_html(),
                'title': "\n".join(
                    grand_child.name.strip()
                    for grand_child in child.get_children()
                    if grand_child.name is not None
                ),
                'progress_status': Progress.to_js_status_str(progress),
                'progress_detail': Progress.to_js_detail_str(progress),
                'type': child.get_icon_class(),
            })

        # Split </script> tags -- browsers handle this as end
        # of script, even if it occurs mid-string. Do this after json.dumps()ing
        # so that we can be sure of the quotations being used
        params = {'items': json.dumps(contents).replace('</script>', '<"+"/script>'),
                  'element_id': self.location.html_id(),
                  'item_id': self.id,
                  'position': self.position,
                  'tag': self.location.category}

        self.content = self.system.render_template('seq_module.html', params)
        self.rendered = True

    def get_icon_class(self):
        child_classes = set(child.get_icon_class() for child in self.get_children())
        new_class = 'other'
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        self.position = 1

        if instance_state is not None:
            state = json.loads(instance_state)
            if 'position' in state:
                self.position = int(state['position'])

        # if position is specified in system, then use that instead
        if system.get('position'):
            self.position = int(system.get('position'))

        self.rendered = False


class SequenceDescriptor(MakoModuleDescriptor, XmlDescriptor):
    mako_template = 'widgets/sequence-edit.html'
    module_class = SequenceModule

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        return {'children': [
            system.process_xml(etree.tostring(child_module)).url
            for child_module in xml_object
        ]}
