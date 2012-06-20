'''
courseware/content_parser.py

This file interfaces between all courseware modules and the top-level course.xml file for a course.

Does some caching (to be explained).

'''

import logging
import os
import sys
import urllib

from lxml import etree
from util.memcache import fasthash

from django.conf import settings

from student.models import UserProfile
from student.models import UserTestGroup
from mitxmako.shortcuts import render_to_string
from util.cache import cache
from multicourse import multicourse_settings
import xmodule

''' This file will eventually form an abstraction layer between the
course XML file and the rest of the system. 

TODO: Shift everything from xml.dom.minidom to XPath (or XQuery)
'''

class ContentException(Exception):
    pass

log = logging.getLogger("mitx.courseware")

def format_url_params(params):
    return [ urllib.quote(string.replace(' ','_')) for string in params ]

def xpath_remove(tree, path):
    ''' Remove all items matching path from lxml tree.  Works in
        place.'''
    items = tree.xpath(path)
    for item in items: 
        item.getparent().remove(item)
    return tree

def id_tag(course):
    ''' Tag all course elements with unique IDs '''
    default_ids = xmodule.get_default_ids()

    # Tag elements with unique IDs
    elements = course.xpath("|".join('//' + c for c in default_ids))
    for elem in elements:
        if elem.get('id'):
            pass
        elif elem.get(default_ids[elem.tag]):
            new_id = elem.get(default_ids[elem.tag])
            # Convert to alphanumeric
            new_id = "".join(a for a in new_id if a.isalnum()) 

            # Without this, a conflict may occur between an html or youtube id
            new_id = default_ids[elem.tag] + new_id
            elem.set('id', new_id)
        else:
            elem.set('id', "id" + fasthash(etree.tostring(elem)))
            
def propogate_downward_tag(element, attribute_name, parent_attribute = None):
    ''' This call is to pass down an attribute to all children. If an element
    has this attribute, it will be "inherited" by all of its children. If a
    child (A) already has that attribute, A will keep the same attribute and
    all of A's children will inherit A's attribute. This is a recursive call.'''

    if (parent_attribute is None):
        #This is the entry call. Select all elements with this attribute
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


def course_xml_process(tree):
    ''' Do basic pre-processing of an XML tree. Assign IDs to all
    items without. Propagate due dates, grace periods, etc. to child
    items. 
    '''
    replace_custom_tags(tree)
    id_tag(tree)
    propogate_downward_tag(tree, "due")
    propogate_downward_tag(tree, "graded")
    propogate_downward_tag(tree, "graceperiod")
    propogate_downward_tag(tree, "showanswer")
    propogate_downward_tag(tree, "rerandomize")
    return tree


def toc_from_xml(dom, active_chapter, active_section):
    '''
    Create a table of contents from the course xml.

    Return format:
    [ {'name': name, 'sections': SECTIONS, 'active': bool}, ... ]

    where SECTIONS is a list
    [ {'name': name, 'format': format, 'due': due, 'active' : bool}, ...]

    active is set for the section and chapter corresponding to the passed
    parameters.  Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.
    '''
    name = dom.xpath('//course/@name')[0]

    chapters = dom.xpath('//course[@name=$name]/chapter', name=name)
    ch = list()
    for c in chapters:
        if c.get('name') == 'hidden':
            continue
        sections = list()
        for s in dom.xpath('//course[@name=$name]/chapter[@name=$chname]/section',
                           name=name, chname=c.get('name')):
            
            format = s.get("subtitle") if s.get("subtitle") else s.get("format") or ""
            active = (c.get("name") == active_chapter and
                      s.get("name") == active_section)

            sections.append({'name': s.get("name") or "", 
                             'format': format, 
                             'due': s.get("due") or "",
                             'active': active})
            
        ch.append({'name': c.get("name"), 
                   'sections': sections,
                   'active': c.get("name") == active_chapter})
    return ch


def replace_custom_tags_dir(tree, dir):
    '''
    Process tree to replace all custom tags defined in dir.
    '''
    tags = os.listdir(dir)
    for tag in tags:
        for element in tree.iter(tag):
            element.tag = 'customtag'
            impl = etree.SubElement(element, 'impl')
            impl.text = tag

def parse_course_file(filename, options, namespace):
    '''
    Parse a course file with the given options, and return the resulting
    xml tree object.
    
    Options should be a dictionary including keys
        'dev_content': bool,
        'groups' : [list, of, user, groups]
    '''
    xml = etree.XML(render_to_string(filename, options, namespace = 'course'))
    return course_xml_process(xml)


def get_section(section, options, dirname):
    '''
    Given the name of a section, an options dict containing keys
    'dev_content' and 'groups', and a directory to look in,
    returns the xml tree for the section, or None if there's no
    such section.
    ''' 
    filename = section + ".xml"

    if filename not in os.listdir(dirname):
        log.error(filename + " not in " + str(os.listdir(dirname)))
        return None

    tree = parse_course_file(filename, options, namespace='sections')
    return tree


def get_module(tree, module, id_tag, module_id, sections_dirname, options):
    '''
    Given the xml tree of the course, get the xml string for a module
    with the specified module type, id_tag, module_id.  Looks in
    sections_dirname for sections.
    ''' 
        # Sanitize input
    if not module.isalnum():
        raise Exception("Module is not alphanumeric")
        
    if not module_id.isalnum():
        raise Exception("Module ID is not alphanumeric")

    # Generate search
    xpath_search='//{module}[(@{id_tag} = "{id}") or (@id = "{id}")]'.format(
        module=module, 
        id_tag=id_tag,
        id=module_id)
    

    result_set = tree.xpath(xpath_search)
    if len(result_set) < 1:
        # Not found in main tree.  Let's look in the section files.
        section_list = (s[:-4] for s in os.listdir(sections_dirname) if s[-4:]=='.xml')
        for section in section_list:
            try: 
                s = get_section(section, options, sections_dirname)
            except etree.XMLSyntaxError: 
                ex = sys.exc_info()
                raise ContentException("Malformed XML in " + section +
                                       "(" + str(ex[1].msg) + ")")
            result_set = s.xpath(xpath_search)
            if len(result_set) != 0:
                break

    if len(result_set) > 1:
        log.error("WARNING: Potentially malformed course file", module, module_id)
        
    if len(result_set)==0:
        log.error('[content_parser.get_module] cannot find %s in course.xml tree',
                      xpath_search)
        log.error('tree = %s' % etree.tostring(tree, pretty_print=True))
        return None

    # log.debug('[courseware.content_parser.module_xml] found %s' % result_set)

    return etree.tostring(result_set[0])






# ==== All Django-specific code below =============================================

def user_groups(user):
    if not user.is_authenticated():
        return []

    # TODO: Rewrite in Django
    key = 'user_group_names_{user.id}'.format(user=user)
    cache_expiration = 60 * 60 # one hour
    
    # Kill caching on dev machines -- we switch groups a lot
    group_names = cache.get(key)
 
    if group_names is None:
        group_names = [u.name for u in UserTestGroup.objects.filter(users=user)]
        cache.set(key, group_names, cache_expiration)

    return group_names


def get_options(user):
    return {'dev_content': settings.DEV_CONTENT, 
            'groups': user_groups(user)}


def replace_custom_tags(tree):
    '''Replace custom tags defined in our custom_tags dir'''
    replace_custom_tags_dir(tree, settings.DATA_DIR+'/custom_tags')


def course_file(user, coursename=None):
    ''' Given a user, return an xml tree object for the course file.

    Handles getting the right file, and processing it depending on the
    groups the user is in.  Does caching of the xml strings.
    '''

    if user.is_authenticated():
        # use user.profile_cache.courseware?
        filename = UserProfile.objects.get(user=user).courseware 
    else:
        filename = 'guest_course.xml'

    # if a specific course is specified, then use multicourse to get
    # the right path to the course XML directory
    if coursename and settings.ENABLE_MULTICOURSE:
        xp = multicourse_settings.get_course_xmlpath(coursename)
        filename = xp + filename	# prefix the filename with the path

    groups = user_groups(user)
    options = get_options(user)

    # Try the cache...
    cache_key = "{0}_processed?dev_content:{1}&groups:{2}".format(
        filename,
        options['dev_content'],
        sorted(groups))
    
    if "dev" in settings.DEFAULT_GROUPS:
        tree_string = None
    else: 
        tree_string = cache.get(cache_key)

    if tree_string:
        tree = etree.XML(tree_string)
    else:
        tree = parse_course_file(filename, options, namespace='course')
        # Cache it
        tree_string = etree.tostring(tree)
        cache.set(cache_key, tree_string, 60)

    return tree


def sections_dir(coursename=None):
    ''' Get directory where sections information is stored.
    '''
    # if a specific course is specified, then use multicourse to get the
    # right path to the course XML directory
    xp = ''
    if coursename and settings.ENABLE_MULTICOURSE:
        xp = multicourse_settings.get_course_xmlpath(coursename)

    return settings.DATA_DIR + xp + '/sections/'
    


def section_file(user, section, coursename=None):
    '''
    Given a user and the name of a section, return that section.
    This is done specific to each course.

    Returns the xml tree for the section, or None if there's no such section.
    '''
    dirname = sections_dir(coursename)


    return get_section(section, options, dirname)


def module_xml(user, module, id_tag, module_id, coursename=None):
    ''' Get XML for a module based on module and module_id. Assumes
        module occurs once in courseware XML file or hidden section.
    ''' 
    tree = course_file(user, coursename)
    sdirname = sections_dir(coursename)
    options = get_options(user)

    return get_module(tree, module, id_tag, module_id, sdirname, options)

