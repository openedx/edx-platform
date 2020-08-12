"""
A plugin manager to retrieve the dynamic course partitions generators.
"""

from openedx.core.lib.plugins import PluginManager


class DynamicPartitionGeneratorsPluginManager(PluginManager):
    NAMESPACE = 'openedx.dynamic_partition_generator'
