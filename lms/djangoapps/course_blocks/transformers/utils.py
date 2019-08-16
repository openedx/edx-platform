"""
Common Helper utilities for transformers
"""
from datetime import datetime, timedelta
import logging

LOG = logging.getLogger(__name__)


def get_field_on_block(block, field_name, default_value=None):
    """
    Get the field value that is directly set on the xblock.
    Do not get the inherited value since field inheritance
    returns value from only a single parent chain
    (e.g., doesn't take a union in DAGs).
    """
    try:
        if block.fields[field_name].is_set_on(block):
            return getattr(block, field_name)
    except KeyError:
        pass
    return default_value


def collect_unioned_set_field(block_structure, transformer, merged_field_name, filter_by):
    """
    Recursively union a set field on the block structure.

    If a block matches filter_by, it will be added to the result set.
    This (potentially empty) set is unioned with the sets contained in
    merged_field_name for all parents of the block.

    This set union operation takes place during a topological traversal
    of the block_structure, so all sets are inherited by descendants.

    Parameters:
        block_structure: BlockStructure to traverse
        transformer: transformer that will be used for get_ and
            set_transformer_block_field
        merged_field_name: name of the field to store
        filter_by: a unary lambda that returns true if a given
            block_key should be included in the result set
    """
    for block_key in block_structure.topological_traversal():
        result_set = {block_key} if filter_by(block_key) else set()
        for parent in block_structure.get_parents(block_key):
            result_set |= block_structure.get_transformer_block_field(
                parent,
                transformer,
                merged_field_name,
                set(),
            )

        block_structure.set_transformer_block_field(
            block_key,
            transformer,
            merged_field_name,
            result_set,
        )


def collect_merged_boolean_field(
        block_structure,
        transformer,
        xblock_field_name,
        merged_field_name,
):
    """
    Collects a boolean xBlock field of name xblock_field_name
    for the given block_structure and transformer.  The boolean
    value is percolated down the hierarchy of the block_structure
    and stored as a value of merged_field_name in the
    block_structure.

    Assumes that the boolean field is False, by default. So,
    the value is ANDed across all parents for blocks with
    multiple parents and ORed across all ancestors down a single
    hierarchy chain.
    """

    for block_key in block_structure.topological_traversal():
        # compute merged value of the boolean field from all parents
        parents = block_structure.get_parents(block_key)
        all_parents_merged_value = all(
            block_structure.get_transformer_block_field(
                parent_key, transformer, merged_field_name, False,
            )
            for parent_key in parents
        ) if parents else False

        # set the merged value for this block
        block_structure.set_transformer_block_field(
            block_key,
            transformer,
            merged_field_name,
            (
                all_parents_merged_value or
                get_field_on_block(
                    block_structure.get_xblock(block_key), xblock_field_name,
                    False,
                )
            )
        )


def collect_merged_date_field(
        block_structure,
        transformer,
        xblock_field_name,
        merged_field_name,
        default_date,
        func_merge_parents=min,
        func_merge_ancestors=max,
):
    """
    Collects a date xBlock field of name xblock_field_name
    for the given block_structure and transformer.  The date
    value is percolated down the hierarchy of the block_structure
    and stored as a value of merged_field_name in the
    block_structure.
    """

    for block_key in block_structure.topological_traversal():

        parents = block_structure.get_parents(block_key)
        block_date = get_field_on_block(block_structure.get_xblock(block_key), xblock_field_name)
        if block_date:
            block_date_cls = type(block_date)
        else:
            block_date_cls = None

        if not parents:
            # no parents so just use value on block or default
            merged_date_value = block_date or default_date

        else:
            parent_dates = [
                block_structure.get_transformer_block_field(
                    parent_key, transformer, merged_field_name, default_date,
                )
                for parent_key in parents
            ]

            if block_date_cls is None:
                if any(isinstance(pdate, timedelta) for pdate in parent_dates):
                    block_date_cls = timedelta
                else:
                    block_date_cls = datetime

            compatible_parent_dates = [pdate for pdate in parent_dates if isinstance(pdate, block_date_cls)]
            if compatible_parent_dates != parent_dates:
                LOG.warning(
                    u"Not all parents of block %s use the same date format: %s != %s",
                    block_key,
                    compatible_parent_dates,
                    parent_dates,
                )

            if compatible_parent_dates:
                # compute merged value of date from all parents
                merged_all_parents_date = func_merge_parents(compatible_parent_dates)

                if not block_date:
                    # no value on this block so take value from parents
                    merged_date_value = merged_all_parents_date

                else:
                    # compute merged date of the block and the parent
                    merged_date_value = func_merge_ancestors(merged_all_parents_date, block_date)
            else:
                merged_date_value = block_date

        block_structure.set_transformer_block_field(
            block_key,
            transformer,
            merged_field_name,
            merged_date_value
        )
