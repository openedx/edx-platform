"""
TODO: something smart here
"""
import logging
from django.utils.translation import ugettext as _
import defusedxml.ElementTree as safe_etree
import pkg_resources

from xblock.core import XBlock

from xblock.fields import XBlockMixin
from xblock.fragment import Fragment
from lxml import etree

logger = logging.getLogger(__name__)

XML_EDITOR_HTML = u'<div id="xml-edit"><textarea class="xml-editor"></textarea></div>'


class AuthoringMixin(XBlockMixin):
    """
    TODO:
    """
    @property
    def editor_tabs(self):
        return [
            {"display_name": "XML", "id": "xml"},
            {"display_name": "Settings", "id": "settings"}
        ]

    def settings_tab_view(self, context=None):
        """
        TODO:
        """
        DEFAULT_FIELDS = [
            'parent',
            'tags',
        ]
        li_template = """
        <li class="field comp-setting-entry is-set">
            <div class="wrapper-comp-setting">
                <label
                    class="label setting-label"
                    for="{input_id}"
                >
                    {key}
                </label>
                <input
                    class="input setting-input"
                    id="{input_id}"
                    value="{input_value}"
                    type="text"
                    tabindex="1"
                >
            </div>
            <span
                class="tip setting-help"
            >
                {help_text}
            </span>
        </li>
        """
        html_strings = []
        html_strings.append('<div class="wrapper-comp-settings is-active editor-with-buttons imagemodal_edit" id="settings-tab">')
        html_strings.append('<ul class="list-input settings-list">')
        for key in self.fields:
            if key not in DEFAULT_FIELDS:
                value = getattr(self, key)
                li = li_template.format(
                    input_id='settings_tab_input__{key}'.format(
                        key=key,
                    ),
                    input_value=value,
                    help_text=self.fields[key].help,
                    key=key,
                )
                html_strings.append(li)
        html_strings.append('</ul>')
        html_strings.append('</div>')
        html_string = unicode('\n'.join(html_strings))
        fragment = Fragment(html_string)
        fragment.add_javascript(pkg_resources.resource_string(__name__, "static/js/src/authoring.js"))
        fragment.initialize_js('SettingsTabView')
        return fragment

    def xml_tab_view(self, context=None):
        """
        Render the XBlock for editing in XML in Studio.
        Args:
            context: Not actively used for this view.
        Returns:
            (Fragment): An HTML fragment for editing the configuration of this XBlock.
        """
        frag = Fragment(XML_EDITOR_HTML)
        frag.add_javascript(pkg_resources.resource_string(__name__, "static/js/src/authoring.js"))
        frag.add_javascript(pkg_resources.resource_string(__name__, "static/js/src/server.js"))
        frag.initialize_js('XBlockXMLEditor')
        return frag

    @XBlock.json_handler
    def update_xml(self, data, suffix=''):
        """
        Update the XBlock's XML.
        Args:
            data (dict): Data from the request; should have a value for the key 'xml'
                containing the XML for this XBlock.
        Kwargs:
            suffix (str): Not used
        Returns:
            dict with keys 'success' (bool) and 'msg' (str)
        """
        if 'xml' in data:
            root = safe_etree.fromstring(data['xml'.encode('utf-8')])
            for key in root.attrib.keys:
                if key in self.fields:
                    setattr(self, key, root.attrib[key])

            return {'success': True, 'msg': _('Successfully updated XBlock')}
        else:
            return {'success': False, 'msg': _('Must specify "xml" in request JSON dict.')}

    @XBlock.json_handler
    def xml(self, data, suffix=''):
        """
        Retrieve the XBlock's content definition, serialized as XML.
        Args:
            data (dict): Not used
        Kwargs:
            suffix (str): Not used
        Returns:
            dict with keys 'success' (bool), 'message' (unicode), and 'xml' (unicode)
        """
        root = etree.Element('root')
        self.add_xml_to_node(root)
        return {'success': True, 'msg': '', 'xml': etree.tostring(root, pretty_print=True)}

    def render_editor_tab_views(self, fragment, context):
        """
        Renders the views for each of the xblock's tab and returns them as a single HTML string. In addition, any
        dependencies are added to the specified fragment.
        """
        html = ""
        for editor_tab in self.editor_tabs:
            view_name = editor_tab['id'] + '_tab_view'
            rendered_child = self.render(view_name, context)
            fragment.add_frag_resources(rendered_child)
            html = html + rendered_child.content

        return html

    def render_tabbed_editor(self, context):
        """
        Renders the Studio preview by rendering each tab desired by the xblock and then rendering
        a view for each one. The client will ensure that only one view is visible at a time.
        """
        fragment = Fragment()
        tab_views = self.render_editor_tab_views(fragment, context)

        fragment.add_content(self.system.render_template('studio_xblock_tabbed_editor.html', {
            'xblock': self,
            'tab_views': tab_views,
        }))

        return fragment

    @XBlock.json_handler
    def save_tab_data(self, data, suffix=''):

        # TODO: try/catch in appropriate place
        for tab in self.editor_tabs:
            tab_data = data[tab[id]]
            if 'fields' in tab_data:
                for key, value in tab_data["fields"]:
                    if key in self.fields:
                        setatrr(self, key, value)
                    else:
                        # TODO: log error
                        pass
            elif 'xml' in tab_data:
                xml = tab_data["xml"]

        self.save()
        return {'success': True, 'msg': _('Successfully saved XBlock')}
