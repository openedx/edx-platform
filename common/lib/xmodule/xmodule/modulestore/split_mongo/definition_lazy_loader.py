from opaque_keys.edx.locator import DefinitionLocator
from bson import SON


class DefinitionLazyLoader(object):
    """
    A placeholder to put into an xblock in place of its definition which
    when accessed knows how to get its content. Only useful if the containing
    object doesn't force access during init but waits until client wants the
    definition. Only works if the modulestore is a split mongo store.
    """
    def __init__(self, modulestore, block_type, definition_id, field_converter):
        """
        Simple placeholder for yet-to-be-fetched data
        :param modulestore: the pymongo db connection with the definitions
        :param definition_locator: the id of the record in the above to fetch
        """
        self.modulestore = modulestore
        self.definition_locator = DefinitionLocator(block_type, definition_id)
        self.field_converter = field_converter

    def fetch(self):
        """
        Fetch the definition. Note, the caller should replace this lazy
        loader pointer with the result so as not to fetch more than once
        """
        return self.modulestore.db_connection.get_definition(self.definition_locator.definition_id)

    def as_son(self):
        return SON((
            ('block_type', self.definition_locator.block_type),
            ('definition', self.definition_locator.definition_id)
        ))
