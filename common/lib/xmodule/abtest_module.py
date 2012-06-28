import json
import random
from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.exceptions import InvalidDefinitionError


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


class ABTestModule(XModule):
    """
    Implements an A/B test with an aribtrary number of competing groups

    Format:
    <abtest>
        <group name="a" portion=".1"><contenta/></group>
        <group name="b" portion=".2"><contentb/></group>
        <default><contentdefault/></default>
    </abtest>
    """

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)

        target_groups = self.definition['data'].keys()
        if shared_state is None:

            self.group = group_from_value(
                self.definition['data']['group_portions'],
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
        print self.group
        return json.dumps({'group': self.group})

    def displayable_items(self):
        return [self.system.get_module(child)
                for child
                in self.definition['data']['group_content'][self.group]]


class ABTestDescriptor(RawDescriptor, XmlDescriptor):
    module_class = ABTestModule

    def __init__(self, system, definition=None, **kwargs):
        kwargs['shared_state_key'] = definition['data']['experiment']
        RawDescriptor.__init__(self, system, definition, **kwargs)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        experiment = xml_object.get('experiment')

        if experiment is None:
            raise InvalidDefinitionError("ABTests must specify an experiment. Not found in:\n{xml}".format(xml=etree.tostring(xml_object, pretty_print=True)))

        definition = {
            'data': {
                'experiment': experiment,
                'group_portions': [],
                'group_content': {None: []},
            },
            'children': []}
        for group in xml_object:
            if group.tag == 'default':
                name = None
            else:
                name = group.get('name')
                definition['data']['group_portions'].append(
                    (name, float(group.get('portion', 0)))
                )

            child_content_urls = [
                system.process_xml(etree.tostring(child)).url
                for child in group
            ]

            definition['data']['group_content'][name] = child_content_urls
            definition['children'].extend(child_content_urls)

        default_portion = 1 - sum(portion for (name, portion) in definition['data']['group_portions'])
        if default_portion < 0:
            raise InvalidDefinitionError("ABTest portions must add up to less than or equal to 1")

        definition['data']['group_portions'].append((None, default_portion))

        return definition
