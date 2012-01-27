try: 
    from django.conf import settings
    from auth.models import UserProfile
except: 
    settings = None 

from lxml import etree

import json
import hashlib
import logging

''' This file will eventually form an abstraction layer between the
course XML file and the rest of the system. 

TODO: Shift everything from xml.dom.minidom to XPath (or XQuery)
'''

log = logging.getLogger("mitx.courseware")

def fasthash(string):
    m = hashlib.new("md4")
    m.update(string)
    return "id"+m.hexdigest()

def xpath(xml, query_string, **args):
    ''' Safe xpath query into an xml tree:
        * xml is the tree.
        * query_string is the query
        * args are the parameters. Substitute for {params}. 
        We should remove this with the move to lxml. 
        We should also use lxml argument passing. '''
    doc = etree.fromstring(xml)
    print type(doc)
    def escape(x):
        # TODO: This should escape the string. For now, we just assume it's made of valid characters. 
        # Couldn't figure out how to escape for lxml in a few quick Googles
        valid_chars="".join(map(chr, range(ord('a'),ord('z')+1)+range(ord('A'),ord('Z')+1)+range(ord('0'), ord('9')+1)))+"_ "
        for e in x:
            if e not in valid_chars:
                raise Exception("Invalid char in xpath expression. TODO: Escape")
        return x

    args=dict( ((k, escape(args[k])) for k in args) )
    print args
    results = doc.xpath(query_string.format(**args))
    return results

def xpath_remove(tree, path):
    ''' Remove all items matching path from lxml tree.  Works in
        place.'''
    items = tree.xpath(path)
    for item in items: 
        item.getparent().remove(item)
    return tree

if __name__=='__main__':
    print xpath('<html><problem name="Bob"></problem></html>', '/{search}/problem[@name="{name}"]', 
                search='html', name="Bob")

def item(l, default="", process=lambda x:x):
    if len(l)==0:
        return default
    elif len(l)==1:
        return process(l[0])
    else:
        raise Exception('Malformed XML')

def id_tag(course):
    ''' Tag all course elements with unique IDs '''
    default_ids = {'video':'youtube',
                   'problem':'filename',
                   'sequential':'id',
                   'html':'filename',
                   'vertical':'id', 
                   'tab':'id',
                   'schematic':'id'}
    
    # Tag elements with unique IDs
    elements = course.xpath("|".join(['//'+c for c in default_ids]))
    for elem in elements:
        if elem.get('id'):
            pass
        elif elem.get(default_ids[elem.tag]):
            new_id = elem.get(default_ids[elem.tag]) 
            new_id = "".join([a for a in new_id if a.isalnum()]) # Convert to alphanumeric
            # Without this, a conflict may occur between an hmtl or youtube id
            new_id = default_ids[elem.tag] + new_id
            elem.set('id', new_id)
        else:
            elem.set('id', fasthash(etree.tostring(elem)))
            
def propogate_downward_tag(element, attribute_name, parent_attribute = None):
    ''' This call is to pass down an attribute to all children. If an element
    has this attribute, it will be "inherited" by all of its children. If a
    child (A) already has that attribute, A will keep the same attribute and
    all of A's children will inherit A's attribute. This is a recursive call.'''
    
    if (parent_attribute == None): #This is the entry call. Select all due elements
        all_attributed_elements = element.xpath("//*[@" + attribute_name +"]")
        for attributed_element in all_attributed_elements:
            attribute_value = attributed_element.get(attribute_name)
            for child_element in attributed_element:
                propogate_downward_tag(child_element, attribute_name, attribute_value)
    else:
        '''The hack below is because we would get _ContentOnlyELements from the
        iterator that can't have due dates set. We can't find API for it. If we
        ever have an element which subclasses BaseElement, we will not tag it'''
        if not element.get(attribute_name) and type(element) == etree._Element:
            element.set(attribute_name, parent_attribute)
            
            for child_element in element:
                propogate_downward_tag(child_element, attribute_name, parent_attribute)
        else:
            #This element would have already been found by Xpath, so we return
            #for now and trust that this element will get its turn to propogate
            #to its children later.
            return
            
def course_file(user):
    # TODO: Cache. 
    tree = etree.parse(settings.DATA_DIR+UserProfile.objects.get(user=user).courseware)
    id_tag(tree)
    propogate_downward_tag(tree, "due")
    propogate_downward_tag(tree, "graded")
    return tree

def module_xml(coursefile, module, id_tag, module_id):
    ''' Get XML for a module based on module and module_id. Assumes
        module occurs once in courseware XML file.. '''
    doc = coursefile

    # Sanitize input
    if not module.isalnum():
        raise Exception("Module is not alphanumeric")
    if not module_id.isalnum():
        raise Exception("Module ID is not alphanumeric")
    xpath_search='//*/{module}[(@{id_tag} = "{id}") or (@id = "{id}")]'.format(module=module, 
                                                           id_tag=id_tag,
                                                           id=module_id)
    #result_set=doc.xpathEval(xpath_search)
    result_set=doc.xpath(xpath_search)
    if len(result_set)>1:
        print "WARNING: Potentially malformed course file", module, module_id
    if len(result_set)==0:
        return None
    return etree.tostring(result_set[0])
    #return result_set[0].serialize()

def toc_from_xml(dom, active_chapter, active_section):
    name = dom.xpath('//course/@name')[0]

    chapters = dom.xpath('//course[@name=$name]/chapter', name=name)
    ch=list()
    for c in chapters:
        if c.get('name') == 'hidden':
            continue
        sections=list()
        for s in dom.xpath('//course[@name=$name]/chapter[@name=$chname]/section', name=name, chname=c.get('name')): 
            sections.append({'name':s.get("name") or "", 
                             'time':s.get("time") or "", 
                             'format':s.get("format") or "", 
                             'due':s.get("due") or "",
                             'active':(c.get("name")==active_chapter and \
                                           s.get("name")==active_section)})
        ch.append({'name':c.get("name"), 
                   'sections':sections,
                   'active':(c.get("name")==active_chapter)})
    return ch

