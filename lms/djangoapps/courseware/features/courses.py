from lettuce import world
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from courseware.courses import get_course_by_id
from xmodule import seq_module, vertical_module

from logging import getLogger
logger = getLogger(__name__)

## support functions
def get_courses():
    '''
    Returns dict of lists of courses available, keyed by course.org (ie university).
    Courses are sorted by course.number.
    '''
    courses = [c for c in modulestore().get_courses()
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)
    return courses

# def get_courseware(course_id):
#     """
#     Given a course_id (string), return a courseware array of dictionaries for the
#     top two levels of navigation. Example:

#     [
#         {'chapter_name': 'Overview',
#             'sections': ['Welcome', 'System Usage Sequence', 'Lab0: Using the tools', 'Circuit Sandbox']
#         },
#         {'chapter_name': 'Week 1',
#             'sections': ['Administrivia and Circuit Elements', 'Basic Circuit Analysis', 'Resistor Divider', 'Week 1 Tutorials']
#             },
#         {'chapter_name': 'Midterm Exam',
#             'sections': ['Midterm Exam']
#         }
#     ]
#     """

#     course = get_course_by_id(course_id)
#     chapters = course.get_children()
#     courseware = [ {'chapter_name':c.display_name, 'sections':[s.display_name for s in c.get_children()]} for c in chapters]
#     return courseware

def get_courseware_with_tabs(course_id):
    """
    Given a course_id (string), return a courseware array of dictionaries for the
    top three levels of navigation. Same as get_courseware() except include
    the tabs on the right hand main navigation page.

    This hides the appropriate courseware as defined by the XML flag test:
    chapter.metadata.get('hide_from_toc','false').lower() == 'true'

    Example:

    [{
        'chapter_name': 'Overview',
        'sections': [{
            'clickable_tab_count': 0,
            'section_name': 'Welcome',
            'tab_classes': []
        }, {
            'clickable_tab_count': 1,
            'section_name': 'System Usage Sequence',
            'tab_classes': ['VerticalDescriptor']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Lab0: Using the tools',
            'tab_classes': ['HtmlDescriptor', 'HtmlDescriptor', 'CapaDescriptor']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Circuit Sandbox',
            'tab_classes': []
        }]
    }, {
        'chapter_name': 'Week 1',
        'sections': [{
            'clickable_tab_count': 4,
            'section_name': 'Administrivia and Circuit Elements',
            'tab_classes': ['VerticalDescriptor', 'VerticalDescriptor', 'VerticalDescriptor', 'VerticalDescriptor']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Basic Circuit Analysis',
            'tab_classes': ['CapaDescriptor', 'CapaDescriptor', 'CapaDescriptor']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Resistor Divider',
            'tab_classes': []
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Week 1 Tutorials',
            'tab_classes': []
        }]
    }, {
        'chapter_name': 'Midterm Exam',
        'sections': [{
            'clickable_tab_count': 2,
            'section_name': 'Midterm Exam',
            'tab_classes': ['VerticalDescriptor', 'VerticalDescriptor']
        }]
    }]
    """

    course = get_course_by_id(course_id)
    chapters = [ chapter for chapter in course.get_children() if chapter.metadata.get('hide_from_toc','false').lower() != 'true' ]
    courseware = [{'chapter_name':c.display_name, 
                    'sections':[{'section_name':s.display_name, 
                                'clickable_tab_count':len(s.get_children()) if (type(s)==seq_module.SequenceDescriptor) else 0, 
                                'tabs':[{'children_count':len(t.get_children()) if (type(t)==vertical_module.VerticalDescriptor) else 0,
                                        'class':t.__class__.__name__  }
                                        for t in s.get_children() ]} 
                                for s in c.get_children() if s.metadata.get('hide_from_toc', 'false').lower() != 'true']}
                    for c in chapters ]

    return courseware

def process_section(element, num_tabs=0):
    '''
    Process section reads through whatever is in 'course-content' and classifies it according to sequence module type.

    This function is recursive

    There are 6 types, with 6 actions.

    Sequence Module
    -contains one child module

    Vertical Module
    -contains other modules
    -process it and get its children, then process them

    Capa Module
    -problem type, contains only one problem
    -for this, the most complex type, we created a separate method, process_problem

    Video Module
    -video type, contains only one video
    -we only check to ensure that a section with class of video exists

    HTML Module
    -html text
    -we do not check anything about it

    Custom Tag Module
    -a custom 'hack' module type
    -there is a large variety of content that could go in a custom tag module, so we just pass if it is of this unusual type

    can be used like this:
    e = world.browser.find_by_css('section.course-content section')
    process_section(e)

    '''
    if element.has_class('xmodule_display xmodule_SequenceModule'):
        logger.debug('####### Processing xmodule_SequenceModule')
        child_modules = element.find_by_css("div>div>section[class^='xmodule']")
        for mod in child_modules:
            process_section(mod)

    elif element.has_class('xmodule_display xmodule_VerticalModule'):
        logger.debug('####### Processing xmodule_VerticalModule')
        vert_list = element.find_by_css("li section[class^='xmodule']")
        for item in vert_list:
            process_section(item)

    elif element.has_class('xmodule_display xmodule_CapaModule'):
        logger.debug('####### Processing xmodule_CapaModule')
        assert element.find_by_css("section[id^='problem']"), "No problems found in Capa Module"
        p = element.find_by_css("section[id^='problem']").first
        p_id = p['id']
        logger.debug('####################')
        logger.debug('id is "%s"' % p_id)
        logger.debug('####################')
        process_problem(p, p_id)

    elif element.has_class('xmodule_display xmodule_VideoModule'):
        logger.debug('####### Processing xmodule_VideoModule')
        assert element.find_by_css("section[class^='video']"), "No video found in Video Module"

    elif element.has_class('xmodule_display xmodule_HtmlModule'):
        logger.debug('####### Processing xmodule_HtmlModule')
        pass

    elif element.has_class('xmodule_display xmodule_CustomTagModule'):
        logger.debug('####### Processing xmodule_CustomTagModule')
        pass

    else:
        assert False, "Class for element not recognized!!"



def process_problem(element, problem_id):
    '''
    Process problem attempts to
    1) scan all the input fields and reset them
    2) click the 'check' button and look for an incorrect response (p.status text should be 'incorrect')
    3) click the 'show answer' button IF it exists and IF the answer is not already displayed
    4) enter the correct answer in each input box
    5) click the 'check' button and verify that answers are correct

    Because of all the ajax calls happening, sometimes the test fails because objects disconnect from the DOM.
    The basic functionality does exist, though, and I'm hoping that someone can take it over and make it super effective.
    '''

    prob_xmod = element.find_by_css("section.problem").first
    input_fields = prob_xmod.find_by_css("section[id^='input']")

    ## clear out all input to ensure an incorrect result
    for field in input_fields:
        field.find_by_css("input").first.fill('')

    ## because of cookies or the application, only click the 'check' button if the status is not already 'incorrect'
    # This would need to be reworked because multiple choice problems don't have this status
    # if prob_xmod.find_by_css("p.status").first.text.strip().lower() != 'incorrect':
    prob_xmod.find_by_css("section.action input.check").first.click()

    ## all elements become disconnected after the click
    ## grab element and prob_xmod because the dom has changed (some classes/elements became hidden and changed the hierarchy)
    # Wait for the ajax reload
    assert world.browser.is_element_present_by_css("section[id='%s']" % problem_id, wait_time=5)
    element = world.browser.find_by_css("section[id='%s']" % problem_id).first
    prob_xmod = element.find_by_css("section.problem").first
    input_fields = prob_xmod.find_by_css("section[id^='input']")
    for field in input_fields:
        assert field.find_by_css("div.incorrect"), "The 'check' button did not work for %s" % (problem_id)

    show_button = element.find_by_css("section.action input.show").first
    ## this logic is to ensure we do not accidentally hide the answers
    if show_button.value.lower() == 'show answer':
        show_button.click()
    else:
        pass

    ## grab element and prob_xmod because the dom has changed (some classes/elements became hidden and changed the hierarchy)
    assert world.browser.is_element_present_by_css("section[id='%s']" % problem_id, wait_time=5)
    element = world.browser.find_by_css("section[id='%s']" % problem_id).first
    prob_xmod = element.find_by_css("section.problem").first
    input_fields = prob_xmod.find_by_css("section[id^='input']")

    ## in each field, find the answer, and send it to the field.
    ## Note that this does not work if the answer type is a strange format, e.g. "either a or b"
    for field in input_fields:
        field.find_by_css("input").first.fill(field.find_by_css("p[id^='answer']").first.text)

    prob_xmod.find_by_css("section.action input.check").first.click()

    ## assert that we entered the correct answers
    ## grab element and prob_xmod because the dom has changed (some classes/elements became hidden and changed the hierarchy)
    assert world.browser.is_element_present_by_css("section[id='%s']" % problem_id, wait_time=5)
    element = world.browser.find_by_css("section[id='%s']" % problem_id).first
    prob_xmod = element.find_by_css("section.problem").first
    input_fields = prob_xmod.find_by_css("section[id^='input']")
    for field in input_fields:
        ## if you don't use 'starts with ^=' the test will fail because the actual class is 'correct ' (with a space)
        assert field.find_by_css("div[class^='correct']"), "The check answer values were not correct for %s" % problem_id
