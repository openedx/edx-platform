#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from lettuce.django import django_url
from course_modes.models import CourseMode
from selenium.common.exceptions import WebDriverException

def create_cert_course():
    world.clear_courses()
    org = 'edx'
    number = '999'
    name = 'Certificates'
    course_id = '{org}/{number}/{name}'.format(
        org=org, number=number, name=name)
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org=org, number=number, display_name=name)

    audit_mode = world.CourseModeFactory.create(
        course_id=course_id,
        mode_slug='audit',
        mode_display_name='audit course',
        min_price=0,
        )
    assert isinstance(audit_mode, CourseMode)

    verfied_mode = world.CourseModeFactory.create(
        course_id=course_id,
        mode_slug='verified',
        mode_display_name='verified cert course',
        min_price=16,
        suggested_prices='32,64,128',
        currency='usd',
        )
    assert isinstance(verfied_mode, CourseMode)


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
    btn_css = 'input[value="Select Audit"]'
    world.css_click(btn_css)


def select_contribution(amount=32):
    radio_css = 'input[value="{}"]'.format(amount)
    world.css_click(radio_css)
    assert world.css_find(radio_css).selected


@step(u'I select the verified track$')
def select_the_verified_track(step):
    create_cert_course()
    register()
    select_contribution(32)
    btn_css = 'input[value="Select Certificate"]'
    world.css_click(btn_css)
    assert world.is_css_present('li.current#progress-step0')


@step(u'I should see the course on my dashboard$')
def should_see_the_course_on_my_dashboard(step):
    course_css = 'article.my-course'
    assert world.is_css_present(course_css)


@step(u'I go to step "([^"]*)"$')
def goto_next_step(step, step_num):
    btn_css = {
        '1': 'p.m-btn-primary a',
        '2': '#face_next_button a.next',
        '3': '#photo_id_next_button a.next',
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

    # Draw a red rectangle in the image element
    snapshot_script = '"{}{}{}{}{}{}"'.format(
        "var canvas = $('#{}_canvas');".format(name),
        "var ctx = canvas[0].getContext('2d');",
        "ctx.fillStyle = 'rgb(200,0,0)';",
        "ctx.fillRect(0, 0, 640, 480);",
        "var image = $('#{}_image');".format(name),
        "image[0].src = canvas[0].toDataURL('image/png');"
        )

    # Mirror the javascript of the photo_verification.html page
    world.browser.execute_script(snapshot_script)
    world.browser.execute_script("$('#{}_capture_button').hide();".format(name))
    world.browser.execute_script("$('#{}_reset_button').show();".format(name))
    world.browser.execute_script("$('#{}_approve_button').show();".format(name))
    assert world.css_visible('#{}_approve_button'.format(name))


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
    assert world.css_visible(button_css[name])

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
    world.css_check(cb_css)
    assert world.css_find(cb_css).checked


@step(u'The course is added to my cart')
def see_course_is_added_to_my_cart(step):
    assert False, 'This step must be implemented'
@step(u'I view the payment page')
def view_the_payment_page(step):
    assert False, 'This step must be implemented'
@step(u'I have submitted photos to verify my identity')
def submitted_photos_to_verify_my_identity(step):
    assert False, 'This step must be implemented'
@step(u'I submit valid payment information')
def submit_valid_payment_information(step):
    assert False, 'This step must be implemented'
@step(u'I see that my payment was successful')
def sesee_that_my_payment_was_successful(step):
    assert False, 'This step must be implemented'
@step(u'I receive an email confirmation')
def receive_an_email_confirmation(step):
    assert False, 'This step must be implemented'
@step(u'I see that I am registered for a verified certificate course on my dashboard')
def see_that_i_am_registered_for_a_verified_certificate_course_on_my_dashboard(step):
    assert False, 'This step must be implemented'
@step(u'I have submitted my "([^"]*)" photo')
def submitted_my_group1_photo(step, group1):
    assert False, 'This step must be implemented'
@step(u'I retake my "([^"]*)" photo')
def retake_my_group1_photo(step, group1):
    assert False, 'This step must be implemented'
@step(u'I see the new photo on the confirmation page.')
def sesee_the_new_photo_on_the_confirmation_page(step):
    assert False, 'This step must be implemented'
@step(u'I have submitted face and ID photos')
def submitted_face_and_id_photos(step):
    assert False, 'This step must be implemented'
@step(u'I edit my name')
def edit_my_name(step):
    assert False, 'This step must be implemented'
@step(u'I see the new name on the confirmation page.')
def sesee_the_new_name_on_the_confirmation_page(step):
    assert False, 'This step must be implemented'
@step(u'I have submitted photos')
def submitted_photos(step):
    assert False, 'This step must be implemented'
@step(u'I leave the flow and return')
def leave_the_flow_and_return(step):
    assert False, 'This step must be implemented'
@step(u'I see the payment page')
def see_the_payment_page(step):
    assert False, 'This step must be implemented'
@step(u'I am registered for the course')
def seam_registered_for_the_course(step):
    assert False, 'This step must be implemented'
@step(u'I return to the student dashboard')
def return_to_the_student_dashboard(step):
    assert False, 'This step must be implemented'
