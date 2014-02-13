"""
Module for Image annotations using annotator.
"""
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String

import textwrap


class AnnotatableFields(object):
    """ Fields for `ImageModule` and `ImageDescriptor`. """
    data = String(help="XML data for the annotation", scope=Scope.content, default=textwrap.dedent("""\
        <annotatable>
            <instructions>
                <p>
                    Add the instructions to the assignment here.
                </p>
            </instructions>
            <p>
                Lorem ipsum dolor sit amet, at amet animal petentium nec. Id augue nemore postulant mea. Ex eam dicant noluisse expetenda, alia admodum abhorreant qui et. An ceteros expetenda mea, tale natum ipsum quo no, ut pro paulo alienum noluisse.
            </p>
        </annotatable>
        """))
    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        scope=Scope.settings,
        default='Image Annotation',
    )
    annotation_storage_url = String(help="Location of Annotation backend", scope=Scope.settings, default="http://your_annotation_storage.com", display_name="Url for Annotation Storage")


class ImageAnnotationModule(AnnotatableFields, XModule):
    '''Image Annotation Module'''
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/html/display.coffee'),
                     resource_string(__name__, 'js/src/annotatable/display.coffee')
                     ],
          'js': []}
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'imageannotation'

    def __init__(self, *args, **kwargs):
        super(ImageAnnotationModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.openseadragonjson = etree.tostring(xmltree, encoding='unicode')

    def _extract_instructions(self, xmltree):
        """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
        instructions = xmltree.find('instructions')
        if instructions is not None:
            instructions.tag = 'div'
            xmltree.remove(instructions)
            return etree.tostring(instructions, encoding='unicode')
        return None

    def get_html(self):
        """ Renders parameters to template. """
        context = {
            'display_name': self.display_name_with_default,
            'instructions_html': self.instructions,
            'annotation_storage': self.annotation_storage_url,
            'openseadragonjson': self.openseadragonjson
        }

        return self.system.render_template('imageannotation.html', context)


class ImageAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    ''' Image annotation descriptor '''
    module_class = ImageAnnotationModule
    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(ImageAnnotationDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            ImageAnnotationDescriptor.annotation_storage_url
        ])
        return non_editable_fields
