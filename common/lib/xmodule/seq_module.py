import json

from lxml import etree

from x_module import XModule, XModuleDescriptor

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']

class ModuleDescriptor(XModuleDescriptor):
    pass

class Module(XModule):
    ''' Layout module which lays out content in a temporal sequence
    '''
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ 'position':self.position })

    @classmethod
    def get_xml_tags(c):
        obsolete_tags = ["sequential", 'tab']
        modern_tags = ["videosequence"]
        return obsolete_tags + modern_tags
        
    def get_html(self):
        self.render()
        return self.content

    def get_init_js(self):
        self.render()
        return self.init_js

    def get_destroy_js(self):
        self.render()
        return self.destroy_js

    def handle_ajax(self, dispatch, get):		# TODO: bounds checking
        ''' get = request.POST instance '''
        if dispatch=='goto_position':
            self.position = int(get['position'])
            return json.dumps({'success':True})
        raise self.system.exception404

    def render(self):
        if self.rendered:
            return
        ## Returns a set of all types of all sub-children
        child_classes = [set([i.tag for i in e.iter()]) for e in self.xmltree]

        titles = ["\n".join([i.get("name").strip() for i in e.iter() if i.get("name") is not None]) \
                       for e in self.xmltree]

        self.contents = self.rendered_children()

        for contents, title in zip(self.contents, titles):
            contents['title'] = title

        for (content, element_class) in zip(self.contents, child_classes):
            new_class = 'other'
            for c in class_priority:
                if c in element_class:
                    new_class = c
            content['type'] = new_class

        # Split </script> tags -- browsers handle this as end
        # of script, even if it occurs mid-string. Do this after json.dumps()ing
        # so that we can be sure of the quotations being used
        params={'items':json.dumps(self.contents).replace('</script>', '<"+"/script>'),
                'id':self.item_id,
                'position': self.position,
                'titles':titles,
                'tag':self.xmltree.tag}

        if self.xmltree.tag in ['sequential', 'videosequence']:
            self.content = self.system.render_template('seq_module.html', params)
        if self.xmltree.tag == 'tab':
            self.content = self.system.render_template('tab_module.html', params)
        self.rendered = True

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        self.xmltree = etree.fromstring(xml)

        self.position = 1

        if state is not None:
            state = json.loads(state)
            if 'position' in state: self.position = int(state['position'])

        # if position is specified in system, then use that instead
        if system.get('position'):
            self.position = int(system.get('position'))

        self.rendered = False


class WeekDescriptor(XModuleDescriptor):

    def get_goals(self):
        """
        Return a list of Goal XModuleDescriptors that are children
        of this Week
        """
        return [child for child in self.get_children() if child.type == 'Goal']

    def get_non_goals(self):
        """
        Return a list of non-Goal XModuleDescriptors that are children of
        this Week
        """
        return [child for child in self.get_children() if child.type != 'Goal']


class SectionDescriptor(XModuleDescriptor):
    pass
