"""
Common Helper utilities for transformers
"""


def get_field_on_block(block, field_name, default_value=None):
    """
    Get the field value that is directly set on the xblock.
    Do not get the inherited value since field inheritance
    returns value from only a single parent chain
    (e.g., doesn't take a union in DAGs).
    """
    if block.fields[field_name].is_set_on(block):
        return getattr(block, field_name)
    else:
        return default_value
