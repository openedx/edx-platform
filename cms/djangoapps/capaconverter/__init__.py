from lxml import etree
import logging
import json
from StringIO import StringIO
import re


class CapaXMLConverter(object):
    class CapaXMLConverterError(BaseException):
        def __init__(self, msg):
            self.msg = msg
            super(CapaXMLConverter.CapaXMLConverterError, self).__init__()

        def __str__(self):
            return self.msg

    class TagNotConsumedError(CapaXMLConverterError):
        pass

    class InvalidNestingError(CapaXMLConverterError):
        pass

    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

        self.end_of_text_tags = ['text', 'endouttext']
        self.group_tags = ['multiplechoiceresponse', 'choiceresponse',
                            'truefalseresponse']
        self.response_tags = ['choice', 'numericalresponse', 'formularesponse', 'stringresponse',
                                'schematicresponse', 'symbolicresponse', 'customresponse']
        self.grouped_tags = ['choice']
        self.script_tags = ['script']
        self.text_included_tags = ['choice', 'schematicresponse', 'customresponse']
        self.attr_copy_tags = ['responseparam']
        self.type_map = {
            'script': 'script',
            'choice': 'choice',
            'multiplechoiceresponse': 'multiple_choice',
            'choiceresponse': 'multiple_choice',
            'truefalseresponse': 'true_false',
            'numericalresponse': 'numerical',
            'stringresponse': 'string',
            'formularesponse': 'formula',
            'schematicresponse': 'schematic',
            'symbolicresponse': 'symbolic',
            'customresponse': 'custom',
            'img': 'image',
            'answer': 'script',
        }
        self.group_children_field = {
            'multiplechoiceresponse': 'choices',
            'choiceresponse': 'choices',
            'truefalseresponse': 'choices',
        }
        self.element_post_hooks = {
            'schematicresponse': self.process_schematicresponse,
            'formularesponse': self.process_formularesponse,
            'customresponse': self.process_customresponse,
        }
        self.all_tags = self.group_tags + self.response_tags + self.script_tags
        self.attribute_rules = {
            '*': [
            ],
            'script': [
                {
                    'src': 'type',
                    'dest': 'language',
                    'wrapper': lambda x: x.split('/')[1].strip(),
                }
            ],
            'customresponse': [
            ],
            'choice': [
                {
                    'src': 'correct',
                    'dest': 'correct',
                    'wrapper': lambda x: x == 'true',
                    'required': True
                },
                {
                    'src': 'location',
                    'dest': 'location',
                },
                {
                    'dest': 'text',
                    'default': '',
                },
            ],
            'answer': [
                {
                    'src': 'type',
                    'dest': 'language',
                    'wrapper': lambda x: x.split('/')[1].strip(),
                }
            ],
            'img': [
                {
                    'src': 'src',
                    'dest': 'url',
                }
            ],
            'numericalresponse': [
                {
                    'src': 'answer',
                    'dest': 'answer',
                }
            ],
            'stringresponse': [
                {
                    'src': 'answer',
                    'dest': 'answer',
                },
            ],
            'schematicresponse': [
                {
                    'src': 'answer',
                    'dest': 'answer',
                }
            ],
            'responseparam': [
                {
                    'src': 'default',
                    'dest': 'tolerance',
                }
            ],
            'formularesponse': [
                {
                    'src': 'samples',
                    'dest': '_samples_',
                }
            ],
        }
        super(CapaXMLConverter, self).__init__()

    def build_from_element(self, element):
        return self.copy_attribute(element, {'type': self.type_map[element.tag], '_tag_': element.tag})

    def copy_attribute(self, element, out):
        rules = self.attribute_rules['*'] + self.attribute_rules.get(element.tag, [])
        for rule in rules:
            if 'src' in rule:
                if rule.get('required', False) or rule['src'] in element.keys():
                    val = element.get(rule['src'])
                    if 'wrapper' in rule:
                        val = rule['wrapper'](val)
                    out[rule['dest']] = val
                elif 'default' in rule:
                    out[rule['dest']] = rule['default']
            elif 'dest' in rule and 'default' in rule:
                out[rule['dest']] = rule['default']
        return out

    def pretty_print(self, data):
        print json.dumps(data, indent=2)

    def dict_del_key(self, d, k):
        if isinstance(d, dict) and k in d:
            del d[k]
        values = d.values() if isinstance(d, dict) else d
        for v in values:
            if isinstance(v, dict) or isinstance(v, list):
                self.dict_del_key(v, k)
        return d

    def feed_post_process_hook(self, element, out):
        if element.tag in self.element_post_hooks:
            out = self.element_post_hooks[element.tag](element, out)
        return out

    def merge_adjacent_string(self, l):
        if l:
            ret = [l[0], ]
            for x in l[1:]:
                if isinstance(ret[-1], basestring) and isinstance(x, basestring):
                    ret[-1] += x
                else:
                    ret.append(x)
            return ret
        return l

    def iterate_element(self, element, ):
        if element.text:
            yield element.text
        for el in element:
            yield el
            if el.tail:
                yield el.tail

    def split_element_on_tag(self, element, tag):
        t = []
        for part in self.iterate_element(element):
            if isinstance(part, basestring) or part.tag == tag:
                t.append(part)
            else:
                t.append(etree.tostring(part, with_tail=False))
        return self.merge_adjacent_string(t)

    # look for only (img, str) or (img, ) in <center> tag
    def picky_center_element_format(self, center):
        img_el_idx, img_el = -1, None
        ret = []
        for el in self.iterate_element(center):
            if not isinstance(el, basestring) and not el.tag == "img":
                return None
            elif isinstance(el, basestring):
                if not el.strip():
                    continue
                if img_el != None:
                    img = self.build_from_element(img_el)
                    img['title'] = el
                    ret.append(img)
                    img_el = None
                else:
                    return None
            elif el.tag == "img":
                if img_el != None:
                    ret.append(self.build_from_element(img_el))
                else:
                    img_el = el
        if img_el != None:
            ret.append(self.build_from_element(img_el))
        return ret

    def convert_xml_file(self, filename):
        out = {'scripts': [], 'contents': []}
        temp = {'text': '', 'section': {}, 'in_text': False, 'embedded_text': False}

        # replace <startouttext /> and <endouttext /> first
        with open(filename, 'r') as f:
            problem_text = f.read()
            problem_text = re.sub("startouttext\s*/", "text", problem_text)
            problem_text = re.sub("endouttext\s*/", "/text", problem_text)
            io = StringIO(problem_text)

        for event, element in etree.iterparse(io, events=('start', 'end')):
            self.logger.debug("%s %s" % ("entering" if event == "start" else "leaving", element))

            if event == 'start':
                if element.tag in self.text_included_tags:
                    temp['embedded_text'] = True

                if element.tag == 'text':
                    temp['in_text'] = True

                    if temp['embedded_text']:
                        # the text is a part of other element, say <choice><text>Choice A</text></choice>
                        t = etree.tostring(element).replace('<text>', '').replace('</text>', '').replace('\n', '')
                        temp['text'] = t
                    else:
                        # or it's individual text. find <center> elements and see if there's image inside
                        # e.g. [x] = ['See the diagram below. \n', <center><img src="" /></center>, 'What's .. ?']
                        for x in self.split_element_on_tag(element, 'center'):
                            if isinstance(x, basestring):
                                out["contents"].append({'type': 'text', 'text': x})
                            else:
                                # self.picky_center_element_format returns a list of {'type': 'image', ...} if 
                                # 
                                ret = self.picky_center_element_format(x)
                                if ret is None:
                                    out["contents"].append({'type': 'text', 'text': etree.tostring(x)})
                                else:
                                    for el in ret:
                                        out["contents"].append(el)

                    element.clear()

                # find response groups and create a group
                elif element.tag in self.group_tags:
                    temp['group'] = self.build_from_element(element)
                    temp['group'][self.group_children_field[element.tag]] = []
                # or it's indivial element
                elif element.tag in self.response_tags + self.script_tags:
                    temp['section'] = self.build_from_element(element) 

            elif event == "end":
                if element.tag in self.text_included_tags:
                    temp['embedded_text'] = False
                    temp['section']['text'] = temp['text']
                    temp['text'] = ''

                # if we want to copy the attributes from this element
                if element.tag in self.attr_copy_tags:
                    self.copy_attribute(element, temp['section'])

                # if it's a script, put text as code and add it into scripts part of output
                if element.tag in self.script_tags:
                    temp['section']['code'] = element.text
                    out['scripts'].append(self.feed_post_process_hook(element, temp['section']))
                    temp['section'] = None

                elif element.tag in self.response_tags:
                    if temp.get('group', None):
                        temp['group'][self.group_children_field[temp['group']['_tag_']]].append(
                            self.feed_post_process_hook(element, temp['section']))
                    else:
                        out['contents'].append(self.feed_post_process_hook(element, temp['section']))
                    temp['section'] = None
                elif element.tag in self.group_tags:
                    out['contents'].append(self.feed_post_process_hook(element, temp['group']))
                    temp['group'] = None

        return (self.dict_del_key(out, '_tag_'))

    def process_customresponse(self, element, out):
        answer_el = element.find('answer')
        answer = self.build_from_element(answer_el)
        answer['code'] = answer_el.text
        out['answer'] = answer
        return out

    def process_schematicresponse(self, element, out):
        answer_el = element.find('answer')
        answer = self.build_from_element(answer_el)
        answer['code'] = answer_el.text
        out['answer'] = answer
        return out

    def process_formularesponse(self, element, out):
        return out
