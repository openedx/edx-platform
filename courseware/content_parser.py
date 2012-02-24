import hashlib
import json
import logging
import os
import re

from datetime import timedelta
from lxml import etree

try: # This lets us do __name__ == ='__main__'
    from django.conf import settings
    from django.core.cache import cache
    from student.models import UserProfile
    from student.models import UserTestGroup
    from mitxmako.shortcuts import render_to_response, render_to_string
except: 
    settings = None 

''' This file will eventually form an abstraction layer between the
course XML file and the rest of the system. 

TODO: Shift everything from xml.dom.minidom to XPath (or XQuery)
'''

log = logging.getLogger("mitx.courseware")


timedelta_regex = re.compile(r'^((?P<days>\d+?) day(?:s?))?(\s)?((?P<hours>\d+?) hour(?:s?))?(\s)?((?P<minutes>\d+?) minute(?:s)?)?(\s)?((?P<seconds>\d+?) second(?:s)?)?$')

def parse_timedelta(time_str):
    parts = timedelta_regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

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
    #print type(doc)
    def escape(x):
        # TODO: This should escape the string. For now, we just assume it's made of valid characters. 
        # Couldn't figure out how to escape for lxml in a few quick Googles
        valid_chars="".join(map(chr, range(ord('a'),ord('z')+1)+range(ord('A'),ord('Z')+1)+range(ord('0'), ord('9')+1)))+"_ "
        for e in x:
            if e not in valid_chars:
                raise Exception("Invalid char in xpath expression. TODO: Escape")
        return x

    args=dict( ((k, escape(args[k])) for k in args) )
    #print args
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
    old_ids = {'video':'youtube',
                   'problem':'filename',
                   'sequential':'id',
                   'html':'filename',
                   'vertical':'id', 
                   'tab':'id',
                   'schematic':'id',
                   'book' : 'id'}
    import courseware.modules
    default_ids = courseware.modules.get_default_ids()

    #print default_ids, old_ids
    #print default_ids == old_ids

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
    
    if (parent_attribute == None): #This is the entry call. Select all elements with this attribute
        all_attributed_elements = element.xpath("//*[@" + attribute_name +"]")
        for attributed_element in all_attributed_elements:
            attribute_value = attributed_element.get(attribute_name)
            for child_element in attributed_element:
                propogate_downward_tag(child_element, attribute_name, attribute_value)
    else:
        '''The hack below is because we would get _ContentOnlyELements from the
        iterator that can't have attributes set. We can't find API for it. If we
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

def user_groups(user):
    # TODO: Rewrite in Django
    key = 'user_group_names_{user.id}'.format(user=user)
    cache_expiration = 60 * 60 * 4 # four hours
    group_names = cache.get(key)
    if group_names is None:
        group_names = [u.name for u in UserTestGroup.objects.filter(users=user)]
        cache.set(key, group_names, cache_expiration)

    return group_names

    # return [u.name for u in UserTestGroup.objects.raw("select * from auth_user, student_usertestgroup, student_usertestgroup_users where auth_user.id = student_usertestgroup_users.user_id and student_usertestgroup_users.usertestgroup_id = student_usertestgroup.id and auth_user.id = %s", [user.id])]

def course_xml_process(tree):
    ''' Do basic pre-processing of an XML tree. Assign IDs to all
    items without. Propagate due dates, grace periods, etc. to child
    items. 
    '''
    id_tag(tree)
    propogate_downward_tag(tree, "due")
    propogate_downward_tag(tree, "graded")
    propogate_downward_tag(tree, "graceperiod")
    return tree

def course_file(user):
    ''' Given a user, return course.xml
    '''
    
    # TODO: Cache.         
    filename = user.profile_cache.courseware # UserProfile.objects.get(user=user).courseware
    groups = user_groups(user)
    options = {'dev_content':settings.DEV_CONTENT, 
               'groups' : groups}

    
    cache_key = filename + "_processed?dev_content:" + str(options['dev_content']) + "&groups:" + str(sorted(groups))
    tree_string = cache.get(cache_key)
    if not tree_string:
        tree = course_xml_process(etree.XML(render_to_string(filename, options, namespace = 'course')))
        tree_string = etree.tostring(tree)
        
        cache.set(cache_key, tree_string, 60)
    else:
        tree = etree.XML(tree_string)

    return tree

def section_file(user, section):
    ''' Given a user and the name of a section, return that section
    '''
    filename = section+".xml"

    if filename not in os.listdir(settings.DATA_DIR + '/sections/'):
        print filename+" not in "+str(os.listdir(settings.DATA_DIR + '/sections/'))
        return None

    options = {'dev_content':settings.DEV_CONTENT, 
               'groups' : user_groups(user)}

    tree = course_xml_process(etree.XML(render_to_string(filename, options, namespace = 'sections')))
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
                             'format':s.get("subtitle") if s.get("subtitle") else s.get("format") or "", 
                             'due':s.get("due") or "",
                             'active':(c.get("name")==active_chapter and \
                                           s.get("name")==active_section)})
        ch.append({'name':c.get("name"), 
                   'sections':sections,
                   'active':(c.get("name")==active_chapter)})
    return ch

