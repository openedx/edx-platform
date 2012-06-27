import json
import random
from lxml import etree

from x_module import XModule, XModuleDescriptor


class ModuleDescriptor(XModuleDescriptor):
    pass


def group_from_value(groups, v):
    ''' Given group: (('a',0.3),('b',0.4),('c',0.3)) And random value
    in [0,1], return the associated group (in the above case, return
    'a' if v<0.3, 'b' if 0.3<=v<0.7, and 'c' if v>0.7
'''
    sum = 0
    for (g, p) in groups:
        sum = sum + p
        if sum > v:
            return g

    # Round off errors might cause us to run to the end of the list
    # If the do, return the last element
    return g


class Module(XModule):
    """
    Implements an A/B test with an aribtrary number of competing groups

    Format:
    <abtest>
        <group name="a" portion=".1"><contenta/></group>
        <group name="b" portion=".2"><contentb/></group>
        <default><contentdefault/></default>
    </abtest>
    """

    def __init__(self, system, xml, item_id, instance_state=None, shared_state=None):
        XModule.__init__(self, system, xml, item_id, instance_state, shared_state)
        self.xmltree = etree.fromstring(xml)

        target_groups = self.xmltree.findall('group')
        if shared_state is None:
            target_values = [
                (elem.get('name'), float(elem.get('portion')))
                for elem in target_groups
            ]
            default_value = 1 - sum(val for (_, val) in target_values)

            self.group = group_from_value(
                target_values + [(None, default_value)],
                random.uniform(0, 1)
            )
        else:
            shared_state = json.loads(shared_state)

            # TODO (cpennington): Remove this once we aren't passing in
            # groups from django groups
            if 'groups' in shared_state:
                self.group = None
                target_names = [elem.get('name') for elem in target_groups]
                for group in shared_state['groups']:
                    if group in target_names:
                        self.group = group
                        break
            else:
                self.group = shared_state['group']

    def get_shared_state(self):
        return json.dumps({'group': self.group})

    def _xml_children(self):
        group = None
        if self.group is None:
            group = self.xmltree.find('default')
        else:
            for candidate_group in self.xmltree.find('group'):
                if self.group == candidate_group.get('name'):
                    group = candidate_group
                    break

        if group is None:
            return []
        return list(group)

    def get_children(self):
        return [self.module_from_xml(child) for child in self._xml_children()]

    def rendered_children(self):
        return [self.render_function(child) for child in self._xml_children()]

    def get_html(self):
        return '\n'.join(child.get_html() for child in self.get_children())
