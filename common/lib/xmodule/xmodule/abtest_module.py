import random
import logging
from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.exceptions import InvalidDefinitionError
from xblock.fields import String, Scope, Dict

DEFAULT = "_DEFAULT_GROUP"


log = logging.getLogger(__name__)


def group_from_value(groups, v):
    """
    Given group: (('a', 0.3), ('b', 0.4), ('c', 0.3)) and random value v
    in [0,1], return the associated group (in the above case, return
    'a' if v < 0.3, 'b' if 0.3 <= v < 0.7, and 'c' if v > 0.7
    """
    sum = 0
    for (g, p) in groups:
        sum = sum + p
        if sum > v:
            return g

    # Round off errors might cause us to run to the end of the list.
    # If the do, return the last element.
    return g


class ABTestFields(object):
    group_portions = Dict(help="What proportions of students should go in each group", default={DEFAULT: 1}, scope=Scope.content)
    group_assignments = Dict(help="What group this user belongs to", scope=Scope.preferences, default={})
    group_content = Dict(help="What content to display to each group", scope=Scope.content, default={DEFAULT: []})
    experiment = String(help="Experiment that this A/B test belongs to", scope=Scope.content)
    has_children = True


class ABTestModule(ABTestFields, XModule):
    """
    Implements an A/B test with an aribtrary number of competing groups
    """

    def __init__(self, *args, **kwargs):
        super(ABTestModule, self).__init__(*args, **kwargs)

        if self.group is None:
            self.group = group_from_value(
                self.group_portions.items(),
                random.uniform(0, 1)
            )

    @property
    def group(self):
        return self.group_assignments.get(self.experiment)

    @group.setter
    def group(self, value):
        self.group_assignments[self.experiment] = value

    @group.deleter
    def group(self):
        del self.group_assignments[self.experiment]

    def get_child_descriptors(self):
        active_locations = set(self.group_content[self.group])
        return [desc for desc in self.descriptor.get_children() if desc.location.to_deprecated_string() in active_locations]

    def displayable_items(self):
        # Most modules return "self" as the displayable_item. We never display ourself
        # (which is why we don't implement get_html). We only display our children.
        return self.get_children()


# TODO (cpennington): Use Groups should be a first class object, rather than being
# managed by ABTests
class ABTestDescriptor(ABTestFields, RawDescriptor, XmlDescriptor):
    module_class = ABTestModule

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        XML Format:
        <abtest experiment="experiment_name">
            <group name="a" portion=".1"><contenta/></group>
            <group name="b" portion=".2"><contentb/></group>
            <default><contentdefault/></default>
        </abtest>
        """
        experiment = xml_object.get('experiment')

        if experiment is None:
            raise InvalidDefinitionError(
                "ABTests must specify an experiment. Not found in:\n{xml}"
                .format(xml=etree.tostring(xml_object, pretty_print=True)))

        group_portions = {}
        group_content = {}
        children = []

        for group in xml_object:
            if group.tag == 'default':
                name = DEFAULT
            else:
                name = group.get('name')
                group_portions[name] = float(group.get('portion', 0))

            child_content_urls = []
            for child in group:
                try:
                    child_block = system.process_xml(etree.tostring(child))
                    child_content_urls.append(child_block.scope_ids.usage_id)
                except:
                    log.exception("Unable to load child when parsing ABTest. Continuing...")
                    continue

            group_content[name] = child_content_urls
            children.extend(child_content_urls)

        default_portion = 1 - sum(
            portion for (name, portion) in group_portions.items()
        )

        if default_portion < 0:
            raise InvalidDefinitionError("ABTest portions must add up to less than or equal to 1")

        group_portions[DEFAULT] = default_portion
        children.sort()

        return {
            'group_portions': group_portions,
            'group_content': group_content,
        }, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('abtest')
        xml_object.set('experiment', self.experiment)
        for name, group in self.group_content.items():
            if name == DEFAULT:
                group_elem = etree.SubElement(xml_object, 'default')
            else:
                group_elem = etree.SubElement(xml_object, 'group', attrib={
                    'portion': str(self.group_portions[name]),
                    'name': name,
                })

            for child_loc in group:
                child = self.system.load_item(child_loc)
                self.runtime.add_block_as_child_node(child, group_elem)

        return xml_object

    def has_dynamic_children(self):
        return True
