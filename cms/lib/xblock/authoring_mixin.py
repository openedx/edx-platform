"""
TODO: something smart here
"""
import copy
import logging
from django.utils.translation import ugettext as _
import defusedxml.ElementTree as safe_etree
import pkg_resources

from xblock.core import XBlock

from xblock.fields import String
from xblock.fields import Scope
from xblock.fields import Integer
from xblock.fields import Float
from xblock.fields import List
from xblock.fields import Dict
from xmodule.fields import RelativeTime
from xblock.fields import XBlockMixin
from xblock.fragment import Fragment
from lxml import etree

logger = logging.getLogger(__name__)

XML_EDITOR_HTML = u'<div id="xml-edit"><textarea class="xml-editor"></textarea></div>'


@XBlock.needs("i18n")
class AuthoringMixin(XBlockMixin):
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
            {"display_name": "XML", "id": "xml"},
            {"display_name": "Settings", "id": "settings"}
        ]

    def settings_tab_view(self, context=None):
        """
        TODO:
        """
        li_template = """
        <li class="field comp-setting-entry is-set">
            <div class="wrapper-comp-setting">
                <label
                    class="label setting-label"
                    for="{input_id}"
                    data-key="{key}"
                >
                    {key_display}
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
        html_strings.append('<div class="wrapper-comp-settings is-active" id="settings-tab">')
        html_strings.append('<ul class="list-input settings-list">')
        html_kvp = {}
        for key in self.editable_metadata_fields:
            value = getattr(self, key)
            key_display = self.fields[key].display_name or key
            li = li_template.format(
                input_id='settings_tab_input__{key}'.format(
                    key=key,
                ),
                input_value=value,
                help_text=self.fields[key].help,
                key_display=key_display,
                key=key,
            )
            html_kvp[key_display] = li
        keys = sorted(html_kvp.keys())
        for key in keys:
            html_strings.append(html_kvp[key])
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

    def update_from_xml(self, xml):
        """
        Update the XBlock's XML.
        Args:
            xml (str): XML String representation used to update the XBlock's field.
        """
        root = safe_etree.fromstring(xml.encode('utf-8'))
        for key in root.attrib.keys:
            if key in self.fields:
                setattr(self, key, root.attrib[key])

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
                    if key in self.fields and isinstance(self.fields[key], String):
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

    @property
    def editable_metadata_fields(self):
        """
        Returns the metadata fields to be edited in Studio. These are fields with scope `Scope.settings`.

        Can be limited by extending `non_editable_metadata_fields`.
        """
        metadata_fields = {}

        # Only use the fields from this class, not mixins
        fields = getattr(self, 'unmixed_class', self.__class__).fields

        for field in fields.values():
            if field.scope == Scope.settings and field not in self.non_editable_metadata_fields:
                metadata_fields[field.name] = self._create_metadata_editor_info(field)
        return metadata_fields

    @property
    def non_editable_metadata_fields(self):
        """
        Return the list of fields that should not be editable in Studio.

        When overriding, be sure to append to the superclasses' list.
        """
        # We are not allowing editing of xblock tag and name fields at this time (for any component).
        return [XBlock.tags, XBlock.name]

    def _create_metadata_editor_info(self, field):
        """
        Creates the information needed by the metadata editor for a specific field.
        """
        def jsonify_value(field, json_choice):
            if isinstance(json_choice, dict):
                json_choice = dict(json_choice)  # make a copy so below doesn't change the original
                if 'display_name' in json_choice:
                    json_choice['display_name'] = get_text(json_choice['display_name'])
                if 'value' in json_choice:
                    json_choice['value'] = field.to_json(json_choice['value'])
            else:
                json_choice = field.to_json(json_choice)
            return json_choice

        def get_text(value):
            """Localize a text value that might be None."""
            if value is None:
                return None
            else:
                return self.runtime.service(self, "i18n").ugettext(value)

        # gets the 'default_value' and 'explicitly_set' attrs
        metadata_field_editor_info = self.runtime.get_field_provenance(self, field)
        metadata_field_editor_info['field_name'] = field.name
        metadata_field_editor_info['display_name'] = get_text(field.display_name)
        metadata_field_editor_info['help'] = get_text(field.help)
        metadata_field_editor_info['value'] = field.read_json(self)

        # We support the following editors:
        # 1. A select editor for fields with a list of possible values (includes Booleans).
        # 2. Number editors for integers and floats.
        # 3. A generic string editor for anything else (editing JSON representation of the value).
        editor_type = "Generic"
        values = field.values
        if isinstance(values, (tuple, list)) and len(values) > 0:
            editor_type = "Select"
            values = [jsonify_value(field, json_choice) for json_choice in values]
        elif isinstance(field, Integer):
            editor_type = "Integer"
        elif isinstance(field, Float):
            editor_type = "Float"
        elif isinstance(field, List):
            editor_type = "List"
        elif isinstance(field, Dict):
            editor_type = "Dict"
        elif isinstance(field, RelativeTime):
            editor_type = "RelativeTime"
        metadata_field_editor_info['type'] = editor_type
        metadata_field_editor_info['options'] = [] if values is None else values

        return metadata_field_editor_info
