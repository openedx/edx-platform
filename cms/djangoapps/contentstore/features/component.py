#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step

data_location = 'i4x://edx/templates'


@step(u'I am on a new unit')
def add_unit(step):
    section_css = 'a.new-courseware-section-button'
    world.css_click(section_css)
    save_section_css = 'input.new-section-name-save'
    world.css_click(save_section_css)
    subsection_css = 'a.new-subsection-item'
    world.css_click(subsection_css)
    save_subsection_css = 'input.new-subsection-name-save'
    world.css_click(save_subsection_css)
    expand_css = 'div.section-item a.expand-collapse-icon'
    world.css_click(expand_css)
    unit_css = 'a.new-unit-item'
    world.css_click(unit_css)


@step(u'I add the following components:')
def add_components(step):
    for component in step.hashes:
        #due to the way lettuce stores the dictionary
        component = component['Component']
        #from pdb import set_trace; set_trace()
        assert component in component_dictionary
        how_to_add = component_dictionary[component]['steps']
        for css in how_to_add:
            world.css_click(css)


@step(u'I see the following components')
def check_components(step):
    for component in step.hashes:
        component = component['Component']
        assert component in component_dictionary
        assert component_dictionary[component]['found']()


@step(u'I delete all components')
def delete_all_components(step):
    components_num = len(component_dictionary)
    for delete in range(0, components_num):
        world.css_click('a.delete-button')


@step(u'I see no components')
def see_no_components(steps):
    assert world.is_css_not_present('li.component')


component_dictionary = {
    'Discussion': {
        'steps': ['a[data-type="discussion"]'],
        'found': lambda: world.is_css_present('section.xmodule_DiscussionModule', wait_time=2)
    },
    'Announcement': {
        'steps': ['a[data-type="html"]', 'a[data-location="%s/html/Announcement"]' % data_location],
        'found': lambda: world.browser.is_text_present('Heading of document')
    },
    'Blank HTML': {
        'steps': ['a[data-type="html"]', 'a[data-location="%s/html/Blank_HTML_Page"]' % data_location],
        'found': lambda: '\n    \n' in [x.html for x in world.css_find('section.xmodule_HtmlModule')]
    },
    'LaTex': {
        'steps': ['a[data-type="html"]', 'a[data-location="%s/html/E-text_Written_in_LaTeX"]' % data_location],
        'found': lambda: world.browser.is_text_present('EXAMPLE: E-TEXT PAGE', wait_time=2)
    },
    'Blank Problem': {
        'steps': ['a[data-type="problem"]', 'a[data-location="%s/problem/Blank_Common_Problem"]' % data_location],
        'found': lambda: world.browser.is_text_present('BLANK COMMON PROBLEM', wait_time=2)
    },
    'Dropdown': {
        'steps': ['a[data-type="problem"]', 'a[data-location="%s/problem/Dropdown"]' % data_location],
        'found': lambda: world.browser.is_text_present('DROPDOWN', wait_time=2)
    },
    'Multi Choice': {
        'steps': ['a[data-type="problem"]', 'a[data-location="%s/problem/Multiple_Choice"]' % data_location],
        'found': lambda: world.browser.is_text_present('MULTIPLE CHOICE', wait_time=2)
    },
    'Numerical': {
        'steps': ['a[data-type="problem"]', 'a[data-location="%s/problem/Numerical_Input"]' % data_location],
        'found': lambda: world.browser.is_text_present('NUMERICAL INPUT', wait_time=2)
    },
    'Text Input': {
        'steps': ['a[data-type="problem"]', 'a[data-location="%s/problem/Text_Input"]' % data_location],
        'found': lambda: world.browser.is_text_present('TEXT INPUT', wait_time=2)
    },
    'Advanced': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Blank_Advanced_Problem"]' % data_location],
        'found': lambda: world.browser.is_text_present('BLANK ADVANCED PROBLEM', wait_time=2)
    },
    'Circuit': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Circuit_Schematic_Builder"]' % data_location],
        'found': lambda: world.browser.is_text_present('CIRCUIT SCHEMATIC BUILDER', wait_time=2)
    },
    'Custom Python': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Custom_Python-Evaluated_Input"]' % data_location],
        'found': lambda: world.browser.is_text_present('CUSTOM PYTHON-EVALUATED INPUT', wait_time=2)
    },
    'Image Mapped': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Image_Mapped_Input"]' % data_location],
        'found': lambda: world.browser.is_text_present('IMAGE MAPPED INPUT', wait_time=2)
    },
    'Math Input': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Math_Expression_Input"]' % data_location],
        'found': lambda: world.browser.is_text_present('MATH EXPRESSION INPUT', wait_time=2)
    },
    'Problem LaTex': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Problem_Written_in_LaTeX"]' % data_location],
        'found': lambda: world.browser.is_text_present('PROBLEM WRITTEN IN LATEX', wait_time=2)
    },
    'Adaptive Hint': {
        'steps': ['a[data-type="problem"]', 'a[id="ui-id-2"]', 'a[data-location="%s/problem/Problem_with_Adaptive_Hint"]' % data_location],
        'found': lambda: world.browser.is_text_present('PROBLEM WITH ADAPTIVE HINT', wait_time=2)
    },
    'Video': {
        'steps': ['a[data-type="video"]'],
        'found': lambda: world.is_css_present('section.xmodule_VideoModule', wait_time=2)
    }
}
