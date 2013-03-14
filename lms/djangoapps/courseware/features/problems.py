from lettuce import world, step
from lettuce.django import django_url
from selenium.webdriver.support.ui import Select
import random
from common import i_am_registered_for_the_course

@step(u'I am viewing a "([^"]*)" problem')
def view_problem(step, problem_type):
    i_am_registered_for_the_course(step, 'edX/model_course/2013_Spring')
    url = django_url(problem_url(problem_type))
    world.browser.visit(url)

@step(u'I answer a "([^"]*)" problem "([^"]*)ly"')
def answer_problem(step, problem_type, correctness):
    assert(correctness in ['correct', 'incorrect'])

    if problem_type == "drop down":
        select_name = "input_i4x-edX-model_course-problem-Drop_Down_Problem_2_1"
        option_text = 'Option 2' if correctness == 'correct' else 'Option 3'
        world.browser.select(select_name, option_text)

    elif problem_type == "multiple choice":
        if correctness == 'correct':
            inputfield('multiple choice', choice='choice_3').check()
        else:
            inputfield('multiple choice', choice='choice_2').check()

    elif problem_type == "checkbox":
        if correctness == 'correct':
            inputfield('checkbox', choice='choice_0').check()
            inputfield('checkbox', choice='choice_2').check()
        else:
            inputfield('checkbox', choice='choice_3').check()

    elif problem_type == 'string':
        textvalue = 'correct string' if correctness == 'correct' else 'incorrect'
        inputfield('string').fill(textvalue)

    elif problem_type == 'numerical':
        textvalue = "pi + 1" if correctness == 'correct' else str(random.randint(-2,2))
        inputfield('numerical').fill(textvalue)

    elif problem_type == 'formula':
        textvalue = "x^2+2*x+y" if correctness == 'correct' else 'x^2'
        inputfield('formula').fill(textvalue)

    check_problem(step)

@step(u'I check a problem')
def check_problem(step):
    world.browser.find_by_css("input.check").click()

@step(u'I reset the problem')
def reset_problem(step):
    world.browser.find_by_css('input.reset').click()

@step(u'My "([^"]*)" answer is marked "([^"]*)"')
def assert_answer_mark(step, problem_type, correctness):
    assert(correctness in ['correct', 'incorrect', 'unanswered'])

    if problem_type == "multiple choice":
        if correctness == 'unanswered':
            mark_classes = ['label.choicegroup_correct', 'label.choicegroup_incorrect',
                            'span.correct', 'span.incorrect']
            for css in mark_classes:
                assert(world.browser.is_element_not_present_by_css(css))
                    
        else:
            if correctness == 'correct':
                mark_class = '.choicegroup_correct'
                assert(world.browser.is_element_present_by_css(mark_class, wait_time=4))

            else:
                # Two ways to be marked incorrect: either applying a 
                # class to the label (marking a particular option)
                # or applying a class to a span (marking the whole problem incorrect)
                mark_classes = ['label.choicegroup_incorrect', 'span.incorrect']
                assert(world.browser.is_element_present_by_css(mark_classes[0], wait_time=4) or
                        world.browser.is_element_present_by_css(mark_classes[1], wait_time=4))

    elif problem_type in ["string", "numerical", "formula"]:
        if correctness == 'unanswered':
            assert(world.browser.is_element_not_present_by_css('div.correct'))
            assert(world.browser.is_element_not_present_by_css('div.incorrect'))
        else:
            mark_class = 'div.correct' if correctness == 'correct' else 'div.incorrect'
            assert(world.browser.is_element_present_by_css(mark_class, wait_time=4))

    else:
        if correctness == 'unanswered':
            assert(world.browser.is_element_not_present_by_css('span.correct'))
            assert(world.browser.is_element_not_present_by_css('span.incorrect'))

        else:
            mark_class = 'span.correct' if correctness == 'correct' else 'span.incorrect'
            assert(world.browser.is_element_present_by_css(mark_class, wait_time=4))

def problem_url(problem_type):
    base = '/courses/edX/model_course/2013_Spring/courseware/Problem_Components/'
    url_extensions = { 'drop down': 'Drop_Down_Problems',
                   'multiple choice': 'Multiple_Choice_Problems',
                    'checkbox': 'Checkbox_Problems', 
                    'string': 'String_Problems',
                    'numerical': 'Numerical_Problems', 
                    'formula': 'Formula_Problems', }

    assert(problem_type in url_extensions)
    return base + url_extensions[problem_type]



def inputfield(problem_type, choice=None):
    field_extensions = { 'drop down': 'Drop_Down_Problem',
                           'multiple choice': 'Multiple_Choice_Problem',
                            'checkbox': 'Checkbox_Problem', 
                            'string': 'String_Problem',
                            'numerical': 'Numerical_Problem', 
                            'formula': 'Formula_Problem', }

    assert(problem_type in field_extensions)
    extension = field_extensions[problem_type]
    sel = "input#input_i4x-edX-model_course-problem-%s_2_1" % extension

    if choice is not None:
        base = "_choice_" if problem_type == "multiple choice" else "_"
        sel = sel + base + str(choice)

    return world.browser.find_by_css(sel)
