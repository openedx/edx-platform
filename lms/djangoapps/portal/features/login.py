from lettuce import step, world
from salad.steps.everything import *
from django.contrib.auth.models import User

@step('I am an unactivated user$')
def i_am_an_unactivated_user(step):
    user_is_an_unactivated_user('robot')

@step('I am an activated user$')
def i_am_an_activated_user(step):
    user_is_an_activated_user('robot')

@step('I submit my credentials on the login form')
def i_submit_my_credentials_on_the_login_form(step):
    fill_in_the_login_form('email', 'robot@edx.org')
    fill_in_the_login_form('password', 'test')
    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_value('Access My Courses').click()
    
@step(u'I should see the login error message "([^"]*)"$')
def i_should_see_the_login_error_message(step, msg):
    login_error_div = world.browser.find_by_css('form#login_form #login_error')
    assert (msg in login_error_div.text)

@step(u'click the dropdown arrow$')
def click_the_dropdown(step):
    css = ".dropdown"
    e = world.browser.find_by_css(css)
    e.click()

#### helper functions

def user_is_an_unactivated_user(uname):
    u = User.objects.get(username=uname)
    u.is_active = False
    u.save()

def user_is_an_activated_user(uname):
    u = User.objects.get(username=uname)
    u.is_active = True
    u.save()

def fill_in_the_login_form(field, value):
    login_form = world.browser.find_by_css('form#login_form')
    form_field = login_form.find_by_name(field)
    form_field.fill(value)
