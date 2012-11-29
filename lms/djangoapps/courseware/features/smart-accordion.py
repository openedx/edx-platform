from lettuce import world, step
from re import sub
from nose.tools import assert_equals
from xmodule.modulestore.django import modulestore
from courses import *

from logging import getLogger
logger = getLogger(__name__)

def check_for_errors():
    e = world.browser.find_by_css('.outside-app')
    if len(e) > 0:
        assert False, 'there was a server error at %s' % (world.browser.url)
    else:
        assert True

@step(u'I verify all the content of each course')
def i_verify_all_the_content_of_each_course(step):
    all_possible_courses = get_courses()
    ids = [c.id for c in all_possible_courses]

    # Get a list of all the registered courses
    registered_courses = world.browser.find_by_css('article.my-course')
    if len(all_possible_courses) < len(registered_courses):
        assert False, "user is registered for more courses than are uniquely posssible"
    else:
        pass

    for test_course in registered_courses:
        test_course.find_by_css('a').click()
        check_for_errors()

        # Get the course. E.g. 'MITx/6.002x/2012_Fall'
        current_course = sub('/info','', sub('.*/courses/', '', world.browser.url))
        validate_course(current_course,ids)

        world.browser.find_link_by_text('Courseware').click()
        assert world.browser.is_element_present_by_id('accordion',wait_time=2)
        check_for_errors()
        browse_course(current_course)

        # clicking the user link gets you back to the user's home page
        world.browser.find_by_css('.user-link').click()
        check_for_errors()

def browse_course(course_id):

    ## count chapters from xml and page and compare
    chapters = get_courseware_with_tabs(course_id)
    num_chapters = len(chapters)

    rendered_chapters = world.browser.find_by_css('#accordion > nav > div')
    num_rendered_chapters = len(rendered_chapters)

    msg = '%d chapters expected, %d chapters found on page for %s' % (num_chapters, num_rendered_chapters, course_id)
    logger.debug(msg)
    assert num_chapters == num_rendered_chapters, msg

    chapter_it = 0

    ## Iterate the chapters
    while chapter_it < num_chapters:

        ## click into a chapter
        world.browser.find_by_css('#accordion > nav > div')[chapter_it].find_by_tag('h3').click()

        ## look for the "there was a server error" div
        check_for_errors()

        ## count sections from xml and page and compare
        sections = chapters[chapter_it]['sections']
        num_sections = len(sections)

        rendered_sections = world.browser.find_by_css('#accordion > nav > div')[chapter_it].find_by_tag('li')
        num_rendered_sections = len(rendered_sections)

        msg = ('%d sections expected, %d sections found on page, %s - %d - %s' %
                (num_sections, num_rendered_sections, course_id, chapter_it, chapters[chapter_it]['chapter_name']))
        logger.debug(msg)
        assert num_sections == num_rendered_sections, msg

        section_it = 0

        ## Iterate the sections
        while section_it < num_sections:

            ## click on a section
            world.browser.find_by_css('#accordion > nav > div')[chapter_it].find_by_tag('li')[section_it].find_by_tag('a').click()

            ## sometimes the course-content takes a long time to load
            assert world.browser.is_element_present_by_css('.course-content',wait_time=5)

            ## look for server error div
            check_for_errors()

            ## count tabs from xml and page and compare

            ## count the number of tabs. If number of tabs is 0, there won't be anything rendered
            ## so we explicitly set rendered_tabs because otherwise find_elements returns a None object with no length
            num_tabs = sections[section_it]['clickable_tab_count']
            if num_tabs != 0:
                rendered_tabs = world.browser.find_by_css('ol#sequence-list > li')
                num_rendered_tabs = len(rendered_tabs)
            else:
                rendered_tabs = 0
                num_rendered_tabs = 0

            msg = ('%d tabs expected, %d tabs found, %s - %d - %s' % 
                        (num_tabs, num_rendered_tabs, course_id, section_it, sections[section_it]['section_name']))
            logger.debug(msg)
            assert num_tabs == num_rendered_tabs, msg

            tabs = sections[section_it]['tabs']
            tab_it = 0

            ## Iterate the tabs
            while tab_it < num_tabs:

                rendered_tabs[tab_it].find_by_tag('a').click()

                ## do something with the tab sections[section_it]
                # e = world.browser.find_by_css('section.course-content section')
                # process_section(e)
                tab_children = tabs[tab_it]['children_count']
                tab_class = tabs[tab_it]['class']
                if tab_children != 0:
                    rendered_items = world.browser.find_by_css('div#seq_content > section > ol > li > section')
                    num_rendered_items = len(rendered_items)              
                    msg = ('%d items expected, %d items found, %s - %d - %s - tab %d' %
                        (tab_children, num_rendered_items, course_id, section_it, sections[section_it]['section_name'], tab_it))
                    logger.debug(msg)
                    assert tab_children == num_rendered_items, msg

                tab_it += 1

            section_it += 1

        chapter_it += 1


def validate_course(current_course, ids):
    try:
        ids.index(current_course)
    except:
        assert False, "invalid course id"
