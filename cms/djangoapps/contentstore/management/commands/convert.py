###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
import json
from lxml import etree


class CapaXMLConverter(object):
    def convert_from_xml(self, filename):
        out = {'scripts': [], 'contents': []}
        temp = {'text':'', 'response':None}
        with open(filename, "r") as f:
            for event, element in etree.iterparse(f, events=("start", "end")):
                if event == "start" and element.tag == "br":
                    temp['text'] += '\n\n'

                elif event == "start" and element.text:
                    temp['text'] += element.text
                elif event == "end" and element.tail:
                    temp['text'] += element.tail

                if event == "start":
                    if element.tag == 'multiplechoiceresponse':
                        temp['group'] = {'type': 'multiple_choice', 'choices': []}
                    elif element.tag == 'truefalseresponse':
                        temp['group'] = {'type': 'true_false', 'statements': []}
                    elif element.tag == "choice":
                        if temp['group']['type'] == 'multiple_choice':
                            temp['response'] = {'type':'choice', 'text': '', 'correct': element.get('correct') == "true"}
                        elif temp['group']['type'] == 'true_false':
                            temp['response'] = {'type':'statement', 'text': '', 'correct': element.get('correct') == "true"}

                elif event == "end":
                    if element.tag == "endouttext":
                        if temp['response']:
                            temp['response']['text'] += temp['text'].strip()
                        else:
                            out['contents'].append({'type':'paragraph', 'text': temp['text'].strip()})
                        temp['text'] = ''
                    elif element.tag in ["multiplechoiceresponse", "truefalseresponse"]:
                        out['contents'].append(temp['group'])
                        temp['group'] = None
                    elif element.tag == "choice":
                        if temp['group']['type'] == 'true_false':
                            temp['group']['statements'].append(temp['response'])
                        elif temp['group']['type'] == 'multiple_choice':
                            temp['group']['choices'].append(temp['response'])
                        temp['response'] = None

        # self.parse_tree(tree, out)
        return out


class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default ModuleStore'''

    def handle(self, *args, **options):
        self.converter = CapaXMLConverter()
        
        # print json.dumps(self.converter.convert_from_xml("/Users/ccp/code/mitx_all/data/6.002x/problems/HW3ID1.xml"), indent=2)
        print json.dumps(self.converter.convert_from_xml("/Users/ccp/code/mitx_all/data/6.002x/problems/multichoice.xml"), indent=2)
