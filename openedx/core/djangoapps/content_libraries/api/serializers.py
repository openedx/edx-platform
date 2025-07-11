"""
Serializer classes for containers
"""
from lxml import etree

from .containers import ContainerMetadata, ContainerType


# WIP: Move this to a separate file
class ContainerSerializer:
    """
    Serializes a container (a Section, Subsection, or Unit) to OLX.
    """
    def __init__(self, container_metadata: ContainerMetadata):
        # self.static_files = []
        self.container_metadata = container_metadata
        olx_node = self._serialize_container(container_metadata)

        self.olx_str = etree.tostring(olx_node, encoding="unicode", pretty_print=True)

    def _serialize_container(self, container_metadata: ContainerMetadata) -> etree.Element:
        """
        Serialize the given container to OLX.
        """
        # Create an XML node to hold the exported data
        container_type = ContainerType(container_metadata.container_key.container_type)

        olx = etree.Element(container_type.olx_tag)
        olx.attrib["id"] = str(container_metadata.container_key)

        # Serialize the container's metadata
        olx.attrib["display_name"] = container_metadata.display_name

        # WIP: Handle static files and children serialization

        return olx
