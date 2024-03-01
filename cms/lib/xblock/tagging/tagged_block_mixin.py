"""
Content tagging functionality for XBlocks.
"""
from urllib.parse import quote, unquote

from xblock.fields import Scope, String


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


class TaggedBlockMixin:
    """
    Mixin containing XML serializing and parsing functionality for tagged blocks
    """

    tags_v1 = String(
        display_name=_("Tags v1"),
        name="tags-v1",
        help=_("Serialized content tags"),
        default="",
        scope=Scope.settings
    )

    def studio_post_duplicate(self, store, source_item):
        """
        Duplicates content tags from the source_item.
        """
        if hasattr(super(), 'studio_post_duplicate'):
            super().studio_post_duplicate()

        if hasattr(source_item, 'serialize_tag_data'):
            tags = source_item.serialize_tag_data()
            self.tags_v1 = tags
        self.add_tags_from_field()

    def serialize_tag_data(self):
        """
        Serialize block's tag data to include in the xml, escaping special characters

        Example tags:
            LightCast Skills Taxonomy: ["Typing", "Microsoft Office"]
            Open Canada Skills Taxonomy: ["MS Office", "<some:;,skill/|=>"]

        Example serialized tags:
            lightcast-skills:Typing,Microsoft Office;open-canada-skills:MS Office,%3Csome%3A%3B%2Cskill%2F%7C%3D%3E
        """
        # This import is done here since we import and use TaggedBlockMixin in the cms settings, but the
        # content_tagging app wouldn't have loaded yet, so importing it outside causes an error
        from openedx.core.djangoapps.content_tagging.api import get_object_tags
        content_tags = get_object_tags(self.scope_ids.usage_id)

        serialized_tags = []
        taxonomies_and_tags = {}
        for tag in content_tags:
            taxonomy_export_id = tag.taxonomy.export_id

            if not taxonomies_and_tags.get(taxonomy_export_id):
                taxonomies_and_tags[taxonomy_export_id] = []

            # Escape special characters in tag values, except spaces (%20) for better readability
            escaped_tag = quote(tag.value).replace("%20", " ")
            taxonomies_and_tags[taxonomy_export_id].append(escaped_tag)

        for taxonomy in taxonomies_and_tags:
            merged_tags = ','.join(taxonomies_and_tags.get(taxonomy))
            serialized_tags.append(f"{taxonomy}:{merged_tags}")

        return ";".join(serialized_tags)

    def add_tags_to_node(self, node):
        """
        Serialize and add tag data (if any) to node
        """
        tag_data = self.serialize_tag_data()
        if tag_data:
            node.set('tags-v1', tag_data)

    def read_tags_from_node(self, node):
        """
        Deserialize and read tag data from node
        """
        if 'tags-v1' in node.attrib:
            self.tags_v1 = str(node.attrib['tags-v1'])

    def add_tags_from_field(self):
        """
        Parse and add tag data from tags_v1 field
        """
        # This import is done here since we import and use TaggedBlockMixin in the cms settings, but the
        # content_tagging app wouldn't have loaded yet, so importing it outside causes an error
        from openedx.core.djangoapps.content_tagging.api import set_object_tags

        tag_data = self.tags_v1
        if not tag_data:
            return

        serialized_tags = tag_data.split(';')
        taxonomy_and_tags_dict = {}
        for serialized_tag in serialized_tags:
            taxonomy_export_id, tags = serialized_tag.split(':')
            tags = tags.split(',')
            tag_values = [unquote(tag) for tag in tags]
            taxonomy_and_tags_dict[taxonomy_export_id] = tag_values

        set_object_tags(self.usage_key, taxonomy_and_tags_dict)
