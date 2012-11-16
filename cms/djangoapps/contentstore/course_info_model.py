from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from lxml import etree
import re
from django.http import HttpResponseBadRequest

## TODO store as array of { date, content } and override  course_info_module.definition_from_xml
## This should be in a class which inherits from XmlDescriptor
def get_course_updates(location):
    """
    Retrieve the relevant course_info updates and unpack into the model which the client expects:
    [{id : location.url() + idx to make unique, date : string, content : html string}]
    """
    try:
        course_updates = modulestore('direct').get_item(location)
    except ItemNotFoundError:
        template = Location(['i4x', 'edx', "templates", 'course_info', "Empty"])
        course_updates = modulestore('direct').clone_item(template, Location(location))

    # current db rep: {"_id" : locationjson, "definition" : { "data" : "<ol>[<li><h2>date</h2>content</li>]</ol>"} "metadata" : ignored}
    location_base = course_updates.location.url()
    
    # purely to handle free formed updates not done via editor. Actually kills them, but at least doesn't break.
    try:
        course_html_parsed = etree.fromstring(course_updates.definition['data'], etree.XMLParser(remove_blank_text=True))
    except etree.XMLSyntaxError:
        course_html_parsed = etree.fromstring("<ol></ol>")
        
    # Confirm that root is <ol>, iterate over <li>, pull out <h2> subs and then rest of val
    course_upd_collection = []
    if course_html_parsed.tag == 'ol':
        # 0 is the oldest so that new ones get unique idx
        for idx, update in enumerate(course_html_parsed.iter("li")):
            if (len(update) == 0):
                continue
            elif (len(update) == 1):
                content = update.find("h2").tail
            else:
                content = etree.tostring(update[1])
                
            course_upd_collection.append({"id" : location_base + "/" + str(idx),
                                          "date" : update.findtext("h2"),
                                          "content" : content})
    # return newest to oldest
    course_upd_collection.reverse()
    return course_upd_collection

def update_course_updates(location, update, passed_id=None):
    """
    Either add or update the given course update. It will add it if the passed_id is absent or None. It will update it if
    it has an passed_id which has a valid value. Until updates have distinct values, the passed_id is the location url + an index
    into the html structure. 
    """
    try:
        course_updates = modulestore('direct').get_item(location)
    except ItemNotFoundError:
        return HttpResponseBadRequest
    
    # purely to handle free formed updates not done via editor. Actually kills them, but at least doesn't break.
    try:
        course_html_parsed = etree.fromstring(course_updates.definition['data'], etree.XMLParser(remove_blank_text=True))
    except etree.XMLSyntaxError:
        course_html_parsed = etree.fromstring("<ol></ol>")

    try:
        new_html_parsed = etree.fromstring(update['content'], etree.XMLParser(remove_blank_text=True))
    except etree.XMLSyntaxError:
        new_html_parsed = None
        
    # Confirm that root is <ol>, iterate over <li>, pull out <h2> subs and then rest of val
    if course_html_parsed.tag == 'ol':
        # ??? Should this use the id in the json or in the url or does it matter?
        if passed_id:
            element = course_html_parsed.findall("li")[get_idx(passed_id)]
            element[0].text = update['date']
            if (len(element) == 1):
                if new_html_parsed is not None:
                    element[0].tail = None
                    element.append(new_html_parsed)
                else:
                    element[0].tail = update['content']
            else:
                if new_html_parsed is not None:
                    element[1] = new_html_parsed
                else:
                    element.pop(1)
                    element[0].tail = update['content']
        else:
            idx = len(course_html_parsed.findall("li"))
            passed_id = course_updates.location.url() + "/" + str(idx)
            element =  etree.SubElement(course_html_parsed, "li")
            date_element = etree.SubElement(element, "h2")
            date_element.text = update['date']
            if new_html_parsed is not None:
                element[1] = new_html_parsed
            else:
                date_element.tail = update['content']
        
        # update db record
        course_updates.definition['data'] = etree.tostring(course_html_parsed)
        modulestore('direct').update_item(location, course_updates.definition['data'])
        
        return {"id" : passed_id,
                "date" : update['date'],
                "content" :update['content']}

def delete_course_update(location, update, passed_id):
    """
    Delete the given course_info update from the db.
    Returns the resulting course_updates b/c their ids change.
    """
    if not passed_id:
        return HttpResponseBadRequest
        
    try:
        course_updates = modulestore('direct').get_item(location)
    except ItemNotFoundError:
        return HttpResponseBadRequest
    
    # TODO use delete_blank_text parser throughout and cache as a static var in a class
    # purely to handle free formed updates not done via editor. Actually kills them, but at least doesn't break.
    try:
        course_html_parsed = etree.fromstring(course_updates.definition['data'], etree.XMLParser(remove_blank_text=True))
    except etree.XMLSyntaxError:
        course_html_parsed = etree.fromstring("<ol></ol>")
        
    if course_html_parsed.tag == 'ol':
        # ??? Should this use the id in the json or in the url or does it matter?
        element_to_delete = course_html_parsed.xpath('/ol/li[position()=' + str(get_idx(passed_id) + 1) + "]")
        if element_to_delete:
            course_html_parsed.remove(element_to_delete[0])

        # update db record
        course_updates.definition['data'] = etree.tostring(course_html_parsed)
        store = modulestore('direct')
        store.update_item(location, course_updates.definition['data'])  
          
    return get_course_updates(location)
    
def get_idx(passed_id):
    """
    From the url w/ idx appended, get the idx.
    """
    # TODO compile this regex into a class static and reuse for each call
    idx_matcher = re.search(r'.*/(\d)+$', passed_id)
    if idx_matcher:
        return int(idx_matcher.group(1))