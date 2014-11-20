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

logger = logging.getLogger(__name__)

XML_EDITOR_HTML = '<div id="xml-edit"><textarea class="xml-editor"></textarea></div>'


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

    def save_editor(self, context=None):
        """
        TODO:
        """
        pass

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
        for key in self.fields:
            if key not in DEFAULT_FIELDS:
                value = getattr(self, key)
                li = li_template.format(
                    input_id='settings_tab_input__{key}'.format(
                        key=key,
                    ),
                    input_value=key,
                    help_text="This name appears in the horizontal navigation at the top of the page.",
                    key=key,
                )
                html_strings.append(li)
        html_string = '\n'.join(html_strings)
        fragment = Fragment(html_string)
        # fragment.add_javascript('')
        # fragment.initialize_js('')
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
        frag.initialize_js('XmlAuthoring')
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
        return self.add_xml_to_node(self)
