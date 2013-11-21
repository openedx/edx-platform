import json
import logging

from lxml import etree

from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.progress import Progress
from xmodule.exceptions import NotFoundError
from xblock.fields import Integer, Scope
from xblock.fragment import Fragment
from pkg_resources import resource_string

log = logging.getLogger(__name__)

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class SequenceFields(object):
    has_children = True

    # NOTE: Position is 1-indexed.  This is silly, but there are now student
    # positions saved on prod, so it's not easy to fix.
    position = Integer(help="Last tab viewed in this sequence", scope=Scope.user_state)


class SequenceModule(SequenceFields, XModule):
    ''' Layout module which lays out content in a temporal sequence
    '''
    js = {'coffee': [resource_string(__name__,
                                     'js/src/sequence/display.coffee')],
          'js': [resource_string(__name__, 'js/src/sequence/display/jquery.sequence.js')]}
    css = {'scss': [resource_string(__name__, 'css/sequence/display.scss')]}
    js_module_name = "Sequence"


    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

        # if position is specified in system, then use that instead
        if getattr(self.system, 'position', None) is not None:
            self.position = int(self.system.position)

    def get_progress(self):
        ''' Return the total progress, adding total done and total available.
        (assumes that each submodule uses the same "units" for progress.)
        '''
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress

    def handle_ajax(self, dispatch, data):  # TODO: bounds checking
        ''' get = request.POST instance '''
        if dispatch == 'goto_position':
            self.position = int(data['position'])
            return json.dumps({'success': True})
        raise NotFoundError('Unexpected dispatch type')

    def student_view(self, context):
        # If we're rendering this sequence, but no position is set yet,
        # default the position to the first element
        if self.position is None:
            self.position = 1

        ## Returns a set of all types of all sub-children
        contents = []

        fragment = Fragment()

        for child in self.get_display_items():
            progress = child.get_progress()
            rendered_child = child.render('student_view', context)
            fragment.add_frag_resources(rendered_child)

            childinfo = {
                'content': rendered_child.content,
                'title': "\n".join(
                    grand_child.display_name
                    for grand_child in child.get_children()
                    if grand_child.display_name is not None
                ),
                'progress_status': Progress.to_js_status_str(progress),
                'progress_detail': Progress.to_js_detail_str(progress),
                'type': child.get_icon_class(),
                'id': child.id,
            }
            if childinfo['title'] == '':
                childinfo['title'] = child.display_name_with_default
            contents.append(childinfo)

        params = {'items': contents,
                  'element_id': self.location.html_id(),
                  'item_id': self.id,
                  'position': self.position,
                  'tag': self.location.category,
                  'ajax_url': self.system.ajax_url,
                  }

        fragment.add_content(self.system.render_template('seq_module.html', params))

        return fragment

    def get_icon_class(self):
        child_classes = set(child.get_icon_class()
                            for child in self.get_children())
        new_class = 'other'
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class


class SequenceDescriptor(SequenceFields, MakoModuleDescriptor, XmlDescriptor):
    mako_template = 'widgets/sequence-edit.html'
    module_class = SequenceModule

    js = {'coffee': [resource_string(__name__, 'js/src/sequence/edit.coffee')]}
    js_module_name = "SequenceDescriptor"

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                children.append(system.process_xml(etree.tostring(child, encoding='unicode')).location.url())
            except Exception as e:
                log.exception("Unable to load child when parsing Sequence. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker("ERROR: " + unicode(e))
                continue
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('sequential')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object
