from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from lxml import etree
from xml.etree import ElementTree as ET

from xblock.fields import Scope, String
import textwrap
from pkg_resources import resource_string

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class ImageExplorerFields(object):
    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        default="Image Explorer"
    )
    data = String(help="XML contents to display for this module", scope=Scope.content, default=textwrap.dedent("""\
        <image_explorer schema_version='1'>
            <background src="//upload.wikimedia.org/wikipedia/commons/thumb/a/ac/MIT_Dome_night1_Edit.jpg/800px-MIT_Dome_night1_Edit.jpg" />
            <description>
                <p>
                    Enjoy using the Image Explorer. Click around the MIT Dome and see what you find!
                </p>
            </description>
            <hotspots>
                <hotspot x='370' y='20'>
                    <feedback width='300' height='170'>
                        <header>
                            <p>
                                This is where many pranks take place. Below are some of the highlights:
                            </p>
                        </header>
                        <body>
                            <ul>
                                <li>Once there was a police car up here</li>
                                <li>Also there was a Fire Truck put up there</li>
                            </ul>
                        </body>
                    </feedback>
                </hotspot>
                <hotspot x='250' y='70'>
                    <feedback width='420' height='360'>
                        <header>
                            <p>
                                Watch the Red Line subway go around the dome
                            </p>
                        </header>
                        <youtube video_id='dmoZXcuozFQ' width='400' height='300' />
                    </feedback>
                </hotspot>
            </hotspots>
        </image_explorer>
        """))



class ImageExplorerModule(ImageExplorerFields, XModule):
    """
    The xModule to render the Image Explorer
    """
    css = {
        'scss': [resource_string(__name__, 'css/image_explorer/display.scss')],
    }

    js = {
        'coffee': [resource_string(__name__, 'js/src/image_explorer/display.coffee')],
    }

    js_module_name = "ImageExplorer"

    def __init__(self, *args, **kwargs):
        super(ImageExplorerModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.description = self._get_description(xmltree)
        self.hotspots = self._get_hotspots(xmltree)
        self.background = self._get_background(xmltree)

    def get_html(self):
        """
        Implementation of the XModule API entry point
        """

        context = {
            'title': self.display_name_with_default,
            'description_html': self.description,
            'hotspots': self.hotspots,
            'background': self.background,
        }

        return self.system.render_template('image_explorer.html', context)

    def _get_background(self, xmltree):
        """
        Parse the XML to get the information about the background image
        """
        background = xmltree.find('background')
        return AttrDict({
            'src': background.get('src'),
            'width': background.get('width'),
            'height': background.get('height')
        })

    def _inner_content(self, tag):
        """
        Helper met
        """
        if tag is not None:
            return u''.join(ET.tostring(e) for e in tag)
        return None

    def _get_description(self, xmltree):
        """
        Parse the XML to get the description information
        """
        description = xmltree.find('description')
        if description is not None:
            return self._inner_content(description)
        return None

    def _get_hotspots(self, xmltree):
        """
        Parse the XML to get the hotspot information
        """
        hotspots_element= xmltree.find('hotspots')
        hotspot_elements = hotspots_element.findall('hotspot')
        hotspots = []
        for hotspot_element in hotspot_elements:
            feedback_element = hotspot_element.find('feedback')

            feedback = AttrDict()
            feedback.width = feedback_element.get('width')
            feedback.height = feedback_element.get('height')
            feedback.header = self._inner_content(feedback_element.find('header'))

            feedback.body = None
            body_element = feedback_element.find('body')
            if body_element is not None:
                feedback.type = 'text'
                feedback.body = self._inner_content(body_element)

            feedback.youtube = None
            youtube_element = feedback_element.find('youtube')
            if youtube_element is not None:
                feedback.type = 'youtube'
                feedback.youtube = AttrDict()
                feedback.youtube.video_id = youtube_element.get('video_id')
                feedback.youtube.width = youtube_element.get('width')
                feedback.youtube.height = youtube_element.get('height')

            hotspot = AttrDict()
            hotspot.feedback = feedback
            hotspot.x = hotspot_element.get('x')
            hotspot.y = hotspot_element.get('y')

            hotspots.append(hotspot)

        return hotspots


class ImageExplorerDescriptor(ImageExplorerFields, RawDescriptor):
    """ Descriptor for custom tags.  Loads the template when created."""
    module_class = ImageExplorerModule
    template_dir_name = 'image_explorer'

    def export_to_file(self):
        """
        Custom tags are special: since they're already pointers, we don't want
        to export them in a file with yet another layer of indirection.
        """
        return False
