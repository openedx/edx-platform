"""
This module provides the abstract base class for all Block Structure
Transformers.
"""
from abc import abstractmethod


class BlockStructureTransformer(object):
    """
    Abstract base class for all block structure transformers.
    """

    # All Transformers are expected to maintain a VERSION class
    # attribute.  While the value for the base class is set to 0,
    # the value for each concrete transformer should be 1 or higher.
    #
    # A transformer's version attribute is used by the block_cache
    # framework in order to determine whether any collected data for a
    # transformer is outdated.  When a transformer's data is collected
    # and cached, it's version number at the time of collection is
    # stored along with the data.  That version number is then checked
    # at the time of accessing the collected data (during the transform
    # phase).
    #
    # The version number of a Transformer should be incremented each
    # time the implementation of its collect method is updated such that
    # its collected data is changed.
    #
    VERSION = 0

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class. It is used to
        identify the transformer's cached data. So it should be unique
        and not conflict with other transformers. Consider using the
        same name that is used in the Transformer Registry. For example,
        for Stevedore, it is specified in the setup.py file.

        Once the transformer is in use and its data is cached, do not
        modify this name value without consideration of backward
        compatibility with previously collected data.
        """
        raise NotImplementedError

    @classmethod
    def collect(cls, block_structure):
        """
        Collects and stores any xBlock and modulestore data into the
        block_structure that's necessary for later execution of the
        transformer's transform method. Transformers should store such
        data in the block_structure using the following methods:
            set_transformer_data
            set_transformer_block_field
            request_xblock_fields

        Transformers can call block_structure.request_xblock_fields for
        any common xBlock fields that should be collected by the
        framework.

        Any full block tree traversals should be implemented in this
        collect phase, leaving the transform phase for fast and direct
        access to a sub-block. If a block's transform output is
        dependent on its ancestors' data, the ancestor's data should be
        percolated down to the descendants. So when a (non-root) block
        is directly accessed in the transform, all of its relevant data
        is readily available (without needing to access its ancestors).

        Traversals of the block_structure can be implemented using the
        following methods:
            topological_traversal
            post_order_traversal

        Arguments:
            block_structure (BlockStructureModulestoreData) - A mutable
                block structure that is to be modified with collected
                data to be cached for the transformer.
        """
        pass

    @abstractmethod
    def transform(self, usage_info, block_structure):
        """
        Transforms the given block_structure for the given usage_info,
        assuming the block_structure contains cached data from a prior
        call to the collect method of the latest version of the
        Transformer.

        No access to the modulestore nor instantiation of xBlocks should
        be performed during the execution of this method. However,
        accesses to user-specific data (outside of the modulestore and
        not via xBlocks) is permitted in order to apply the transform
        for the given usage_info.

        Note: The root of the given block_structure is not necessarily
        the same as the root of the block_structure passed to the prior
        collect method. The collect method is given the top-most root
        of the structure, while the transform method may be called upon
        any sub-structure or even a single block within the originally
        collected structure.

        A Transformer may choose to remove entire sub-structures during
        the transform method and may do so using the remove_block and
        remove_block_if methods.

        Amongst the many methods available for a block_structure, the
        following methods are commonly used during transforms:
            get_xblock_field
            get_transformer_data
            get_transformer_block_field
            remove_block
            remove_block_if
            topological_traversal
            post_order_traversal

        Arguments:
            usage_info (any negotiated type) - A usage-specific object
                that is passed to the block_cache and forwarded to all
                requested Transformers in order to apply a
                usage-specific transform. For example, an instance of
                usage_info would contain a user object for which the
                transform should be applied.

            block_structure (BlockStructureBlockData) - A mutable
                block structure, with already collected data for the
                transformer, that is to be transformed in place.
        """
        pass
