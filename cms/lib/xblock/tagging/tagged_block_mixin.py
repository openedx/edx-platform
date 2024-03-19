"""
Content tagging functionality for XBlocks.
"""
from urllib.parse import quote, unquote


class TaggedBlockMixin:
    """
    Mixin containing XML serializing and parsing functionality for tagged blocks
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the tagged xblock.
        """
        # We store tags internally, without an XBlock field, because we don't want tags to be stored to the modulestore.
        # But we do want them persisted on duplicate, copy, or export/import.
        self.tags_v1 = ""

    @property
    def tags_v1(self) -> str:
        """
        Returns the serialized tags.
        """
        return self._tags_v1

    @tags_v1.setter
    def tags_v1(self, tags: str) -> None:
        """
        Returns the serialized tags.
        """
        self._tags_v1 = tags

    @classmethod
    def serialize_tag_data(cls, usage_id):
        """
        Serialize a block's tag data to include in the xml, escaping special characters

        Example tags:
            LightCast Skills Taxonomy: ["Typing", "Microsoft Office"]
            Open Canada Skills Taxonomy: ["MS Office", "<some:;,skill/|=>"]

        Example serialized tags:
            lightcast-skills:Typing,Microsoft Office;open-canada-skills:MS Office,%3Csome%3A%3B%2Cskill%2F%7C%3D%3E
        """
        # This import is done here since we import and use TaggedBlockMixin in the cms settings, but the
        # content_tagging app wouldn't have loaded yet, so importing it outside causes an error
        from openedx.core.djangoapps.content_tagging.api import get_object_tags
        content_tags = get_object_tags(usage_id)

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
        tag_data = self.serialize_tag_data(self.scope_ids.usage_id)
        if tag_data:
            node.set('tags-v1', tag_data)

    def add_tags_from_field(self):
        """
        Parse tags_v1 data and create tags for this block.
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

    def add_xml_to_node(self, node):
        """
        Include the serialized tag data in XML when adding to node
        """
        super().add_xml_to_node(node)
        self.add_tags_to_node(node)

    def studio_post_duplicate(self, store, source_item) -> bool:
        """
        Duplicates content tags from the source_item.

        Returns False to indicate the children have not been handled.
        """
        if hasattr(super(), 'studio_post_duplicate'):
            super().studio_post_duplicate()

        self.tags_v1 = self.serialize_tag_data(source_item.scope_ids.usage_id)
        self.add_tags_from_field()
        return False

    def studio_post_paste(self, store, source_node) -> bool:
        """
        Copies content tags from the source_node.

        Returns False to indicate the children have not been handled.
        """
        if hasattr(super(), 'studio_post_paste'):
            super().studio_post_paste()

        if 'tags-v1' in source_node.attrib:
            self.tags_v1 = str(source_node.attrib['tags-v1'])

        self.add_tags_from_field()
        return False
