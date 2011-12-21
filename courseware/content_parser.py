from django.conf import settings
from xml.dom.minidom import parse, parseString
import libxml2

''' This file will eventually form an abstraction layer between the
course XML file and the rest of the system. 

TODO: Shift everything from xml.dom.minidom to XPath (or XQuery)
'''

def module_xml(module, id_tag, module_id):
    ''' Get XML for a module based on module and module_id. Assumes
        module occurs once in course.xml. '''
    doc = libxml2.parseFile(settings.DATA_DIR+'course.xml')

    # Sanitize input
    if not module.isalnum():
        raise Exception("Module is not alphanumeric")
    if not module_id.isalnum():
        raise Exception("Module ID is not alphanumeric")
    xpath_search='//*/{module}[@{id_tag} = "{id}"]'.format(module=module, 
                                                           id_tag=id_tag,
                                                           id=module_id)
    result_set=doc.xpathEval(xpath_search)
    if len(result_set)>1:
        print "WARNING: Potentially malformed course file", module, module_id
    if len(result_set)==0:
        return None
    return result_set[0].serialize()

def toc_from_xml(active_chapter,active_section):
    dom=parse(settings.DATA_DIR+'course.xml')

    course = dom.getElementsByTagName('course')[0]
    name=course.getAttribute("name")
    chapters = course.getElementsByTagName('chapter')
    ch=list()
    for c in chapters:
        sections=list()
        for s in c.getElementsByTagName('section'):
            sections.append({'name':s.getAttribute("name"), 
                             'time':s.getAttribute("time"), 
                             'format':s.getAttribute("format"), 
                             'due':s.getAttribute("due"),
                             'active':(c.getAttribute("name")==active_chapter and \
                                           s.getAttribute("name")==active_section)})
        ch.append({'name':c.getAttribute("name"), 
                   'sections':sections,
                   'active':(c.getAttribute("name")==active_chapter)})
    return ch

def dom_select(dom, element_type, element_name):
    if dom==None:
        return None
    elements=dom.getElementsByTagName(element_type)
    for e in elements:
        if e.getAttribute("name")==element_name:
            return e
    return None

