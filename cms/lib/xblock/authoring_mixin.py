"""
TODO: something smart here
"""
import copy
import logging
from django.utils.translation import ugettext as _
import defusedxml.ElementTree as safe_etree
import pkg_resources

from xblock.core import XBlock

from xblock.fields import XBlockMixin
from xblock.fragment import Fragment
from lxml import etree
import json

logger = logging.getLogger(__name__)

# Uck, this needs to go into a shared location.
from xmodule.x_module import MetadataEditingMixin
from mako.template import Template

XML_EDITOR_HTML = u'<div id="xml-edit"><textarea class="xml-editor">{xml}</textarea></div>'


@XBlock.needs("i18n")
class AuthoringMixin(MetadataEditingMixin, XBlockMixin):
    """
    TODO:
    """
    _services_requested = {
        "i18n": "need",
    }

    @property
    def editor_tabs(self):
        return [
            # TODO: internationalize
            {"display_name": "Settings", "id": "settings"},
        ]

    def settings_tab_view(self, context=None):
        """
        TODO:
        """
        settings_template = Template("""
        <%!
        import json
        # Uck, don't really want this import.
        from xmodule.modulestore import EdxJSONEncoder
        %>
        <div class="wrapper-comp-settings metadata_edit is-active" id="settings-tab" data-metadata='${json.dumps(metadata_fields, cls=EdxJSONEncoder) | h}'/>
        """)
        fragment = Fragment(settings_template.render(metadata_fields=self.editable_metadata_fields))
        fragment.add_javascript(pkg_resources.resource_string(__name__, "static/js/src/authoring.js"))
        fragment.initialize_js('SettingsTabViewInit')
        return fragment

    def xml_tab_view(self, context=None):
        """
        Render the XBlock for editing in XML in Studio.
        Args:
            context: Not actively used for this view.
        Returns:
            (Fragment): An HTML fragment for editing the configuration of this XBlock.
        """
        root = etree.Element('root')
        self.add_xml_to_node(root)
        xml = etree.tostring(root, pretty_print=True)
        frag = Fragment(XML_EDITOR_HTML.format(xml=xml))
        frag.add_javascript(pkg_resources.resource_string(__name__, "static/js/src/authoring.js"))
        frag.initialize_js('XBlockXMLEditor')
        return frag

    def update_from_xml(self, xml):
        """
        Update the XBlock's XML.
        Args:
            xml (str): XML String representation used to update the XBlock's field.
        """
        root = safe_etree.fromstring(xml.encode('utf-8'))
        for key in root.attrib.keys():
            if key in self.fields:
                setattr(self, key, root.attrib[key])

    def render_tabbed_editor(self, context):
        """
        Renders the Studio preview by rendering each tab desired by the xblock and then rendering
        a view for each one. The client will ensure that only one view is visible at a time.
        """
        fragment = Fragment()
        if self.editor_tabs and len(self.editor_tabs) > 0:
            tabs = copy.deepcopy(self.editor_tabs)
            current_tab = tabs[0]
            for tab in tabs:
                view_name = tab['id'] + '_tab_view'
                rendered_child = self.render(view_name, context)
                fragment.add_frag_resources(rendered_child)
                tab['rendered_view'] = rendered_child.content

            fragment.add_content(self.system.render_template('studio_xblock_tabbed_editor.html', {
                'xblock': self,
                'tabs': tabs,
                'current_tab_id': current_tab['id']
            }))
        else:
            raise Exception("Unable to render tabs for xblock")

        return fragment

    @XBlock.json_handler
    def save_tab_data(self, data, suffix=''):

        # TODO: try/catch in appropriate place
        # for tab in self.editor_tabs:
        for tab in data:
            tab_data = data[tab]
            if 'fields' in tab_data:
                for key, value in tab_data["fields"].iteritems():
                    if key in self.fields:
                        setattr(self, key, value)
                    else:
                        logger.error(
                            "Field {field} not a valid field for XBlock.".format(field=key)
                        )
            elif 'xml' in tab_data:
                self.update_from_xml(tab_data["xml"])

        self.save()
        # TODO: return validation messages.
        return {'success': True, 'msg': _('Successfully saved XBlock')}
