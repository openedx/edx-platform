from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from courseware.courses import get_course_by_id
from xmodule import seq_module

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

def get_courseware(course_id):
    """
    Given a course_id (string), return a courseware array of dictionaries for the
    top two levels of navigation. Example:

    [
        {'chapter_name': 'Overview',
            'sections': ['Welcome', 'System Usage Sequence', 'Lab0: Using the tools', 'Circuit Sandbox']
        },
        {'chapter_name': 'Week 1',
            'sections': ['Administrivia and Circuit Elements', 'Basic Circuit Analysis', 'Resistor Divider', 'Week 1 Tutorials']
            },
        {'chapter_name': 'Midterm Exam',
            'sections': ['Midterm Exam']
        }
    ]
    """

    course = get_course_by_id(course_id)
    chapters = course.get_children()
    courseware = [ {'chapter_name':c.display_name, 'sections':[s.display_name for s in c.get_children()]} for c in chapters]
    return courseware

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
    courseware = [{'chapter_name':c.display_name, 'sections':[{'section_name':s.display_name, 'clickable_tab_count': len(s.get_children()) if (type(s)==seq_module.SequenceDescriptor) else 0, 'tab_classes':[t.__class__.__name__ for t in s.get_children() ]} for s in c.get_children() if s.metadata.get('hide_from_toc', 'false').lower() != 'true']} for c in chapters ]

    return courseware

