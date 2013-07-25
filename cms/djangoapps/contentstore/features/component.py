#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_true

DATA_LOCATION = 'i4x://edx/templates'


@step(u'I am editing a new unit')
def add_unit(step):
    css_selectors = ['a.new-courseware-section-button', 'input.new-section-name-save', 'a.new-subsection-item',
                    'input.new-subsection-name-save', 'div.section-item a.expand-collapse-icon', 'a.new-unit-item']
    for selector in css_selectors:
        world.css_click(selector)


@step(u'I add the following components:')
def add_components(step):
    for component in [step_hash['Component'] for step_hash in step.hashes]:
        assert component in COMPONENT_DICTIONARY
        for css in COMPONENT_DICTIONARY[component]['steps']:
            world.css_click(css)


@step(u'I see the following components')
def check_components(step):
    for component in [step_hash['Component'] for step_hash in step.hashes]:
        assert component in COMPONENT_DICTIONARY
        assert_true(COMPONENT_DICTIONARY[component]['found_func'](), "{} couldn't be found".format(component))


@step(u'I delete all components')
def delete_all_components(step):
    for _ in range(len(COMPONENT_DICTIONARY)):
        world.css_click('a.delete-button')


@step(u'I see no components')
def see_no_components(steps):
    assert world.is_css_not_present('li.component')


@step(u'I delete a component')
def delete_one_component(step):
    world.css_click('a.delete-button')


@step(u'I edit and save a component')
def edit_and_save_component(step):
    world.css_click('.edit-button')
    world.css_click('.save-button')


def step_selector_list(data_type, path, index=1):
    selector_list = ['a[data-type="{}"]'.format(data_type)]
    if index != 1:
        selector_list.append('a[id="ui-id-{}"]'.format(index))
    if path is not None:
        selector_list.append('a[data-location="{}/{}/{}"]'.format(DATA_LOCATION, data_type, path))
    return selector_list


def found_text_func(text):
    return lambda: world.browser.is_text_present(text)


def found_css_func(css):
    return lambda: world.is_css_present(css, wait_time=2)

COMPONENT_DICTIONARY = {
    'Discussion': {
        'steps': step_selector_list('discussion', None),
        'found_func': found_css_func('section.xmodule_DiscussionModule')
    },
    'Blank HTML': {
        'steps': step_selector_list('html', 'Blank_HTML_Page'),
        #this one is a blank html so a more refined search is being done
        'found_func': lambda: '\n    \n' in [x.html for x in world.css_find('section.xmodule_HtmlModule')]
    },
    'LaTex': {
        'steps': step_selector_list('html', 'E-text_Written_in_LaTeX'),
        'found_func': found_text_func('EXAMPLE: E-TEXT PAGE')
    },
    'Blank Problem': {
        'steps': step_selector_list('problem', 'Blank_Common_Problem'),
        'found_func': found_text_func('BLANK COMMON PROBLEM')
    },
    'Dropdown': {
        'steps': step_selector_list('problem', 'Dropdown'),
        'found_func': found_text_func('DROPDOWN')
    },
    'Multi Choice': {
        'steps': step_selector_list('problem', 'Multiple_Choice'),
        'found_func': found_text_func('MULTIPLE CHOICE')
    },
    'Numerical': {
        'steps': step_selector_list('problem', 'Numerical_Input'),
        'found_func': found_text_func('NUMERICAL INPUT')
    },
    'Text Input': {
        'steps': step_selector_list('problem', 'Text_Input'),
        'found_func': found_text_func('TEXT INPUT')
    },
    'Advanced': {
        'steps': step_selector_list('problem', 'Blank_Advanced_Problem', index=2),
        'found_func': found_text_func('BLANK ADVANCED PROBLEM')
    },
    'Circuit': {
        'steps': step_selector_list('problem', 'Circuit_Schematic_Builder', index=2),
        'found_func': found_text_func('CIRCUIT SCHEMATIC BUILDER')
    },
    'Custom Python': {
        'steps': step_selector_list('problem', 'Custom_Python-Evaluated_Input', index=2),
        'found_func': found_text_func('CUSTOM PYTHON-EVALUATED INPUT')
    },
    'Image Mapped': {
        'steps': step_selector_list('problem', 'Image_Mapped_Input', index=2),
        'found_func': found_text_func('IMAGE MAPPED INPUT')
    },
    'Math Input': {
        'steps': step_selector_list('problem', 'Math_Expression_Input', index=2),
        'found_func': found_text_func('MATH EXPRESSION INPUT')
    },
    'Problem LaTex': {
        'steps': step_selector_list('problem', 'Problem_Written_in_LaTeX', index=2),
        'found_func': found_text_func('PROBLEM WRITTEN IN LATEX')
    },
    'Adaptive Hint': {
        'steps': step_selector_list('problem', 'Problem_with_Adaptive_Hint', index=2),
        'found_func': found_text_func('PROBLEM WITH ADAPTIVE HINT')
    },
    'Video': {
        'steps': step_selector_list('video', None),
        'found_func': found_css_func('section.xmodule_VideoModule')
    }
}
