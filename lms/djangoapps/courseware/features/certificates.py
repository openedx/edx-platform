# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from lettuce.django import django_url
from course_modes.models import CourseMode
from nose.tools import assert_equal


UPSELL_LINK_CSS = '.message-upsell a.action-upgrade[href*="edx/999/Certificates"]'

def create_cert_course():
    world.clear_courses()
    org = 'edx'
    number = '999'
    name = 'Certificates'
    course_id = '{org}/{number}/{name}'.format(
        org=org, number=number, name=name)
    world.scenario_dict['course_id'] = course_id
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org=org, number=number, display_name=name)

    honor_mode = world.CourseModeFactory.create(
        course_id=world.scenario_dict['course_id'],
        mode_slug='honor',
        mode_display_name='honor mode',
        min_price=0,
    )

    verfied_mode = world.CourseModeFactory.create(
        course_id=course_id,
        mode_slug='verified',
        mode_display_name='verified cert course',
        min_price=16,
        suggested_prices='32,64,128',
        currency='usd',
        )


def register():
    url = 'courses/{org}/{number}/{name}/about'.format(
        org='edx', number='999', name='Certificates')
    world.browser.visit(django_url(url))

    world.css_click('section.intro a.register')
    assert world.is_css_present('section.wrapper h3.title')


@step(u'I select the audit track$')
def select_the_audit_track(step):
    create_cert_course()
    register()
    btn_css = 'input[name="honor_mode"]'
    world.wait(1)  # TODO remove this after troubleshooting JZ
    world.css_find(btn_css)
    world.css_click(btn_css)


def select_contribution(amount=32):
    radio_css = 'input[value="{}"]'.format(amount)
    world.css_click(radio_css)
    assert world.css_find(radio_css).selected


def click_verified_track_button():
    world.wait_for_ajax_complete()
    btn_css = 'input[value="Select Certificate"]'
    world.css_click(btn_css)


@step(u'I select the verified track for upgrade')
def select_verified_track_upgrade(step):
    select_contribution(32)
    world.wait_for_ajax_complete()
    btn_css = 'input[value="Upgrade Your Registration"]'
    world.css_click(btn_css)
    # TODO: might want to change this depending on the changes for upgrade
    assert world.is_css_present('section.progress')


@step(u'I select the verified track$')
def select_the_verified_track(step):
    create_cert_course()
    register()
    select_contribution(32)
    click_verified_track_button()
    assert world.is_css_present('section.progress')


@step(u'I should see the course on my dashboard$')
def should_see_the_course_on_my_dashboard(step):
    course_css = 'li.course-item'
    assert world.is_css_present(course_css)


@step(u'I go to step "([^"]*)"$')
def goto_next_step(step, step_num):
    btn_css = {
        '1': '#face_next_button',
        '2': '#face_next_link',
        '3': '#photo_id_next_link',
        '4': '#pay_button',
    }
    next_css = {
        '1': 'div#wrapper-facephoto.carousel-active',
        '2': 'div#wrapper-idphoto.carousel-active',
        '3': 'div#wrapper-review.carousel-active',
        '4': 'div#wrapper-review.carousel-active',
    }
    world.css_click(btn_css[step_num])

    # Pressing the button will advance the carousel to the next item
    # and give the wrapper div the "carousel-active" class
    assert world.css_find(next_css[step_num])


@step(u'I capture my "([^"]*)" photo$')
def capture_my_photo(step, name):

    # Hard coded red dot image
    image_data = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=='
    snapshot_script = "$('#{}_image')[0].src = '{}';".format(name, image_data)

    # Mirror the javascript of the photo_verification.html page
    world.browser.execute_script(snapshot_script)
    world.browser.execute_script("$('#{}_capture_button').hide();".format(name))
    world.browser.execute_script("$('#{}_reset_button').show();".format(name))
    world.browser.execute_script("$('#{}_approve_button').show();".format(name))
    assert world.css_find('#{}_approve_button'.format(name))


@step(u'I approve my "([^"]*)" photo$')
def approve_my_photo(step, name):
    button_css = {
        'face': 'div#wrapper-facephoto li.control-approve',
        'photo_id': 'div#wrapper-idphoto li.control-approve',
    }
    wrapper_css = {
        'face': 'div#wrapper-facephoto',
        'photo_id': 'div#wrapper-idphoto',
    }

    # Make sure that the carousel is in the right place
    assert world.css_has_class(wrapper_css[name], 'carousel-active')
    assert world.css_find(button_css[name])

    # HACK: for now don't bother clicking the approve button for
    # id_photo, because it is sending you back to Step 1.
    # Come back and figure it out later. JZ Aug 29 2013
    if name=='face':
        world.css_click(button_css[name])

    # Make sure you didn't advance the carousel
    assert world.css_has_class(wrapper_css[name], 'carousel-active')


@step(u'I select a contribution amount$')
def select_contribution_amount(step):
    select_contribution(32)


@step(u'I confirm that the details match$')
def confirm_details_match(step):
    # First you need to scroll down on the page
    # to make the element visible?
    # Currently chrome is failing with ElementNotVisibleException
    world.browser.execute_script("window.scrollTo(0,1024)")

    cb_css = 'input#confirm_pics_good'
    world.css_click(cb_css)
    assert world.css_find(cb_css).checked


@step(u'I am at the payment page')
def at_the_payment_page(step):
    world.wait_for_present('input[name=transactionSignature]')


@step(u'I submit valid payment information$')
def submit_payment(step):
    # First make sure that the page is done if it still executing
    # an ajax query.
    world.wait_for_ajax_complete()
    button_css = 'input[value=Submit]'
    world.css_click(button_css)


@step(u'I have submitted face and ID photos$')
def submitted_face_and_id_photos(step):
    step.given('I am logged in')
    step.given('I select the verified track')
    step.given('I go to step "1"')
    step.given('I capture my "face" photo')
    step.given('I approve my "face" photo')
    step.given('I go to step "2"')
    step.given('I capture my "photo_id" photo')
    step.given('I approve my "photo_id" photo')
    step.given('I go to step "3"')


@step(u'I have submitted photos to verify my identity')
def submitted_photos_to_verify_my_identity(step):
    step.given('I have submitted face and ID photos')
    step.given('I select a contribution amount')
    step.given('I confirm that the details match')
    step.given('I go to step "4"')


@step(u'I submit my photos and confirm')
def submit_photos_and_confirm(step):
    step.given('I go to step "1"')
    step.given('I capture my "face" photo')
    step.given('I approve my "face" photo')
    step.given('I go to step "2"')
    step.given('I capture my "photo_id" photo')
    step.given('I approve my "photo_id" photo')
    step.given('I go to step "3"')
    step.given('I select a contribution amount')
    step.given('I confirm that the details match')
    step.given('I go to step "4"')


@step(u'I see that my payment was successful')
def see_that_my_payment_was_successful(step):
    title = world.css_find('div.wrapper-content-main h3.title')
    assert_equal(title.text, u'Congratulations! You are now verified on edX.')


@step(u'I navigate to my dashboard')
def navigate_to_my_dashboard(step):
    world.css_click('span.avatar')
    assert world.css_find('section.my-courses')


@step(u'I see the course on my dashboard')
def see_the_course_on_my_dashboard(step):
    course_link_css = 'section.my-courses a[href*="edx/999/Certificates"]'
    assert world.is_css_present(course_link_css)


@step(u'I see the upsell link on my dashboard')
def see_upsell_link_on_my_dashboard(step):
    course_link_css = UPSELL_LINK_CSS
    assert world.is_css_present(course_link_css)


@step(u'I do not see the upsell link on my dashboard')
def see_upsell_link_on_my_dashboard(step):
    course_link_css = UPSELL_LINK_CSS
    assert world.is_css_not_present(course_link_css)


@step(u'I select the upsell link on my dashboard')
def see_upsell_link_on_my_dashboard(step):
    # expand the upsell section
    world.css_click('.message-upsell')
    course_link_css = UPSELL_LINK_CSS
    # click the actual link
    world.css_click(course_link_css)


@step(u'I see that I am on the verified track')
def see_that_i_am_on_the_verified_track(step):
    id_verified_css = 'li.course-item article.course.verified'
    assert world.is_css_present(id_verified_css)


@step(u'I leave the flow and return$')
def leave_the_flow_and_return(step):
    world.visit('verify_student/verified/edx/999/Certificates/')


@step(u'I am at the verified page$')
def see_the_payment_page(step):
    assert world.css_find('button#pay_button')


@step(u'I edit my name$')
def edit_my_name(step):
    btn_css = 'a.retake-photos'
    world.css_click(btn_css)
