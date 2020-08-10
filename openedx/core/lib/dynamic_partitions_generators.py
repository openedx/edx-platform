"""
A plugin manager to retrieve the dynamic course partitions generators.
"""

from edx_django_utils.plugins import PluginManager


class DynamicPartitionGeneratorsPluginManager(PluginManager):
    NAMESPACE = 'openedx.dynamic_partition_generator'
