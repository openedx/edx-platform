# -*- coding: utf-8 -*-
"""
Discussion XBlock
"""
import logging

from django.templatetags.static import static
from django.utils.translation import get_language_bidi

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xmodule.raw_module import RawDescriptor

from xblock.core import XBlock
from xblock.fields import Scope, String, UNIQUE_ID
from xblock.fragment import Fragment
from xmodule.xml_module import XmlParserMixin

from openedx.core.lib.xblock_builtin import get_css_dependencies, get_js_dependencies


log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


@XBlock.needs('user')
@XBlock.needs('i18n')
class DiscussionXBlock(XBlock, StudioEditableXBlockMixin, XmlParserMixin):
    """
    Provides a discussion forum that is inline with other content in the courseware.
    """
    discussion_id = String(scope=Scope.settings, default=UNIQUE_ID)
    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        default="Discussion",
        scope=Scope.settings
    )
    discussion_category = String(
        display_name=_("Category"),
        default=_("Week 1"),
        help=_(
            "A category name for the discussion. "
            "This name appears in the left pane of the discussion forum for the course."
        ),
        scope=Scope.settings
    )
    discussion_target = String(
        display_name=_("Subcategory"),
        default="Topic-Level Student-Visible Label",
        help=_(
            "A subcategory name for the discussion. "
            "This name appears in the left pane of the discussion forum for the course."
        ),
        scope=Scope.settings
    )
    sort_key = String(scope=Scope.settings)

    editable_fields = ["display_name", "discussion_category", "discussion_target"]

    has_author_view = True  # Tells Studio to use author_view

    # support for legacy OLX format - consumed by XmlParserMixin.load_metadata
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['id'] = 'discussion_id'
    metadata_translations['for'] = 'discussion_target'

    @property
    def course_key(self):
        """
        :return: int course id

        NB: The goal is to move this XBlock out of edx-platform, and so we use
        scope_ids.usage_id instead of runtime.course_id so that the code will
        continue to work with workbench-based testing.
        """
        return getattr(self.scope_ids.usage_id, 'course_key', None)

    @property
    def django_user(self):
        """
        Returns django user associated with user currently interacting
        with the XBlock.
        """
        user_service = self.runtime.service(self, 'user')
        if not user_service:
            return None
        return user_service._django_user  # pylint: disable=protected-access

    @staticmethod
    def vendor_js_dependencies():
        """
        Returns list of vendor JS files that this XBlock depends on.

        The helper function that it uses to obtain the list of vendor JS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        return get_js_dependencies('discussion_vendor')

    @staticmethod
    def js_dependencies():
        """
        Returns list of JS files that this XBlock depends on.

        The helper function that it uses to obtain the list of JS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        return get_js_dependencies('discussion')

    @staticmethod
    def css_dependencies():
        """
        Returns list of CSS files that this XBlock depends on.

        The helper function that it uses to obtain the list of CSS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        if get_language_bidi():
            return get_css_dependencies('style-inline-discussion-rtl')
        else:
            return get_css_dependencies('style-inline-discussion')

    def add_resource_urls(self, fragment):
        """
        Adds URLs for JS and CSS resources that this XBlock depends on to `fragment`.
        """
        # Head dependencies
        for vendor_js_file in self.vendor_js_dependencies():
            fragment.add_resource_url(static(vendor_js_file), "application/javascript", "head")

        for css_file in self.css_dependencies():
            fragment.add_css_url(static(css_file))

        # Body dependencies
        for js_file in self.js_dependencies():
            fragment.add_javascript_url(static(js_file))

    def has_permission(self, permission):
        """
        Encapsulates lms specific functionality, as `has_permission` is not
        importable outside of lms context, namely in tests.

        :param user:
        :param str permission: Permission
        :rtype: bool
        """
        # normal import causes the xmodule_assets command to fail due to circular import - hence importing locally
        from django_comment_client.permissions import has_permission  # pylint: disable=import-error

        return has_permission(self.django_user, permission, self.course_key)

    def student_view(self, context=None):
        """
        Renders student view for LMS.
        """
        fragment = Fragment()

        self.add_resource_urls(fragment)

        context = {
            'discussion_id': self.discussion_id,
            'display_name': self.display_name if (self.display_name) else _("Discussion"),
            'user': self.django_user,
            'course_id': self.course_key,
            'discussion_category': self.discussion_category,
            'discussion_target': self.discussion_target,
            'can_create_thread': self.has_permission("create_thread"),
            'can_create_comment': self.has_permission("create_comment"),
            'can_create_subcomment': self.has_permission("create_sub_comment"),
        }

        fragment.add_content(self.runtime.render_template('discussion/_discussion_inline.html', context))
        fragment.initialize_js('DiscussionInlineBlock')

        return fragment

    def author_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders author view for Studio.
        """
        fragment = Fragment()
        fragment.add_content(self.runtime.render_template(
            'discussion/_discussion_inline_studio.html',
            {'discussion_id': self.discussion_id}
        ))
        return fragment

    def student_view_data(self):
        """
        Returns a JSON representation of the student_view of this XBlock.
        """
        return {'topic_id': self.discussion_id}

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Parses OLX into XBlock.

        This method is overridden here to allow parsing legacy OLX, coming from discussion XModule.
        XBlock stores all the associated data, fields and children in a XML element inlined into vertical XML file
        XModule stored only minimal data on the element included into vertical XML and used a dedicated "discussion"
        folder in OLX to store fields and children. Also, some info was put into "policy.json" file.

        If no external data sources are found (file in "discussion" folder), it is exactly equivalent to base method
        XBlock.parse_xml. Otherwise this method parses file in "discussion" folder (known as definition_xml), applies
        policy.json and updates fields accordingly.
        """
        block = super(DiscussionXBlock, cls).parse_xml(node, runtime, keys, id_generator)

        cls._apply_translations_to_node_attributes(block, node)
        cls._apply_metadata_and_policy(block, node, runtime)

        return block

    @classmethod
    def _apply_translations_to_node_attributes(cls, block, node):
        """
        Applies metadata translations for attributes stored on an inlined XML element.
        """
        for old_attr, target_attr in cls.metadata_translations.iteritems():
            if old_attr in node.attrib and hasattr(block, target_attr):
                setattr(block, target_attr, node.attrib[old_attr])

    @classmethod
    def _apply_metadata_and_policy(cls, block, node, runtime):
        """
        Attempt to load definition XML from "discussion" folder in OLX, than parse it and update block fields
        """
        try:
            definition_xml, _ = cls.load_definition_xml(node, runtime, block.scope_ids.def_id)
        except Exception as err:  # pylint: disable=broad-except
            log.info(
                "Exception %s when trying to load definition xml for block %s - assuming XBlock export format",
                err,
                block
            )
            return

        metadata = cls.load_metadata(definition_xml)
        cls.apply_policy(metadata, runtime.get_policy(block.scope_ids.usage_id))

        for field_name, value in metadata.iteritems():
            if field_name in block.fields:
                setattr(block, field_name, value)
