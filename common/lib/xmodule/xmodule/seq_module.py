import json
import logging

from lxml import etree

from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.progress import Progress
from xmodule.exceptions import NotFoundError
from .model import Int, Scope
from pkg_resources import resource_string

log = logging.getLogger("mitx.common.lib.seq_module")

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']

def display_name(module):
    if hasattr(module, 'display_name'):
        return module.display_name

    if hasattr(module, 'lms'):
        return module.lms.display_name

class SequenceModule(XModule):
    ''' Layout module which lays out content in a temporal sequence
    '''
    js = {'coffee': [resource_string(__name__,
                                     'js/src/sequence/display.coffee')],
          'js': [resource_string(__name__, 'js/src/sequence/display/jquery.sequence.js')]}
    css = {'scss': [resource_string(__name__, 'css/sequence/display.scss')]}
    js_module_name = "Sequence"

    has_children = True

    # NOTE: Position is 1-indexed.  This is silly, but there are now student
    # positions saved on prod, so it's not easy to fix.
    position = Int(help="Last tab viewed in this sequence", scope=Scope.student_state)

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

        # if position is specified in system, then use that instead
        if self.system.get('position'):
            self.position = int(self.system.get('position'))

        # Default to the first child
        # Don't set 1 as the default in the property definition, because
        # there is code that looks for the existance of the position value
        # to determine if the student has visited the sequence before or not
        if self.position is None:
            self.position = 1

        self.rendered = False

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
        if dispatch == 'goto_position':
            self.position = int(get['position'])
            return json.dumps({'success': True})
        raise NotFoundError('Unexpected dispatch type')

    def render(self):
        if self.rendered:
            return
        ## Returns a set of all types of all sub-children
        contents = []
        for child in self.get_display_items():
            progress = child.get_progress()
            childinfo = {
                'content': child.get_html(),
                'title': "\n".join(
                    display_name(grand_child)
                    for grand_child in child.get_children()
                    if display_name(grand_child) is not None
                ),
                'progress_status': Progress.to_js_status_str(progress),
                'progress_detail': Progress.to_js_detail_str(progress),
                'type': child.get_icon_class(),
                'id': child.id,
            }
            if childinfo['title']=='':
                childinfo['title'] = display_name(child)
            contents.append(childinfo)

        params = {'items': contents,
                  'element_id': self.location.html_id(),
                  'item_id': self.id,
                  'position': self.position,
                  'tag': self.location.category
                  }

        self.content = self.system.render_template('seq_module.html', params)
        self.rendered = True

    def get_icon_class(self):
        child_classes = set(child.get_icon_class()
                            for child in self.get_children())
        new_class = 'other'
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class


class SequenceDescriptor(MakoModuleDescriptor, XmlDescriptor):
    mako_template = 'widgets/sequence-edit.html'
    module_class = SequenceModule

    has_children = True
    stores_state = True  # For remembering where in the sequence the student is

    js = {'coffee': [resource_string(__name__, 'js/src/sequence/edit.coffee')]}
    js_module_name = "SequenceDescriptor"

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                children.append(system.process_xml(etree.tostring(child)).location.url())
            except Exception, e:
                log.exception("Unable to load child when parsing Sequence. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker("ERROR: " + str(e))
                continue
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('sequential')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object

