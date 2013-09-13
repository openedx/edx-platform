"""
CME Registration methods
"""

import json
import logging
from statsd import statsd

from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from django.core.validators import validate_email, validate_slug, ValidationError
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.core.mail import send_mail

from student.models import Registration
from cme_registration.models import CmeUserProfile
from mitxmako.shortcuts import render_to_response, render_to_string


log = logging.getLogger("mitx.student")


@ensure_csrf_cookie
def cme_register_user(request, extra_context=None):
    """
    This view will display the non-modal registration form which has been customised
    from the standard registration form for CME.
    """
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    context = {
        'course_id': request.GET.get('course_id'),
        'enrollment_action': request.GET.get('enrollment_action'),
        'patient_population_choices': PATIENT_POPULATION_CHOICES,
        'specialty_choices': SPECIALTY_CHOICES,
        'sub_specialty_choices': SUB_SPECIALTY_CHOICES
    }
    if extra_context is not None:
        context.update(extra_context)

    return render_to_response('cme_register.html', context)


@ensure_csrf_cookie
def cme_create_account(request, post_override=None):
    '''
    JSON call to create new edX account; modified for the CME registration form.
    Used by form in signup_modal.html, which is included into navigation.html
    '''
    json_string = {'success': False}

    post_vars = post_override if post_override else request.POST

    # Confirm we have a properly formed request
    for var in ['username', 'email', 'password', 'name']:
        if var not in post_vars:
            json_string['value'] = "Error (401 {field}). E-mail us.".format(field=var)
            json_string['field'] = var
            return HttpResponse(json.dumps(json_string))

    #Validate required felds
    error = validate_required_fields(post_vars)
    if error is not None:
        return HttpResponse(json.dumps(error))

    #Validate required check boxes
    error = validate_required_boxes(post_vars)
    if error is not None:
        return HttpResponse(json.dumps(error))

    #Validate required radio buttons
    error = validate_required_radios(post_vars)
    if error is not None:
        return HttpResponse(json.dumps(error))

    #Validate required secondary fields
    error = validate_required_secondaries(post_vars)
    if error is not None:
        return HttpResponse(json.dumps(error))

    #Validate email address
    try:
        validate_email(post_vars['email'])
    except ValidationError:
        json_string['value'] = "Valid e-mail is required."
        json_string['field'] = 'email'
        return HttpResponse(json.dumps(json_string))

    #Validate username conforms
    try:
        validate_slug(post_vars['username'])
    except ValidationError:
        json_string['value'] = "Username should only consist of A-Z and 0-9, with no spaces."
        json_string['field'] = 'username'
        return HttpResponse(json.dumps(json_string))

    # Ok, looks like everything is legit.  Create the account.
    ret = _do_cme_create_account(post_vars)
    if isinstance(ret, HttpResponse):  # if there was an error then return that
        return ret
    (user, cme_user_profile, registration) = ret

    email_dict = {
        'name': post_vars['name'],
        'key': registration.activation_key,
    }

    # composes activation email
    subject = render_to_string('emails/activation_email_subject.txt', email_dict)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt', email_dict)

    try:
        if settings.MITX_FEATURES.get('REROUTE_ACTIVATION_EMAIL'):
            dest_addr = settings.MITX_FEATURES['REROUTE_ACTIVATION_EMAIL']
            message = ("Activation for %s (%s): %s\n" % (user, user.email, cme_user_profile.name) +
                       '-' * 80 + '\n\n' + message)
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [dest_addr], fail_silently=False)
        else:
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    except:
        log.warning('Unable to send activation email to user', exc_info=True)
        json_string['value'] = 'Could not send activation e-mail.'
        return HttpResponse(json.dumps(json_string))

    # Immediately after a user creates an account, we log them in. They are only
    # logged in until they close the browser. They can't log in again until they click
    # the activation link from the email.
    login_user = authenticate(username=post_vars['username'], password=post_vars['password'])
    login(request, login_user)
    request.session.set_expiry(0)

    statsd.increment("common.student.account_created")

    json_string = {'success': True}
    HttpResponse(json.dumps(json_string), mimetype="application/json")

    response = HttpResponse(json.dumps({'success': True}))
    return response


def _do_cme_create_account(post_vars):
    """
    Given cleaned post variables, create the User, UserProfile and CmeUserProfile objects, as well as the
    registration for this user.

    Returns a tuple (User, CmeUserProfile, Registration).
    Since CmeUserProfile is implemented using multi-table inheritence of UserProfile, the CmeUserProfile object
    will also contain all the UserProfile fields.
    """
    user = User(username=post_vars['username'],
                email=post_vars['email'],
                is_active=False)
    user.set_password(post_vars['password'])
    registration = Registration()
    # @todo: Rearrange so that if part of the process fails, the whole process fails.
    # Right now, we can have e.g. no registration e-mail sent out and a zombie account
    try:
        user.save()
    except IntegrityError:
        json_string = {'success': False}
        # Figure out the cause of the integrity error
        if len(User.objects.filter(username=post_vars['username'])) > 0:
            json_string['value'] = "An account with the Public Username  '" + post_vars['username'] + "' already exists."
            json_string['field'] = 'username'
            return HttpResponse(json.dumps(json_string))

        if len(User.objects.filter(email=post_vars['email'])) > 0:
            json_string['value'] = "An account with the Email '" + post_vars['email'] + "' already exists."
            json_string['field'] = 'email'
            return HttpResponse(json.dumps(json_string))

    registration.register(user)

    cme_user_profile = CmeUserProfile(user=user)

    #UserProfile fields
    cme_user_profile.name = post_vars['name']

    #CmeUserProfile fields
    cme_user_profile.profession = post_vars.get('profession')
    cme_user_profile.professional_designation = post_vars.get('professional_designation')
    cme_user_profile.license_number = post_vars.get('license_number')
    cme_user_profile.organization = post_vars.get('organization')
    cme_user_profile.stanford_affiliated = True if post_vars.get('stanford_affiliated') == '1' else False

    if post_vars.get('how_stanford_affiliated') == 'Other':
        cme_user_profile.how_stanford_affiliated = post_vars.get('how_stanford_affiliated_free')
    else:
        cme_user_profile.how_stanford_affiliated = post_vars.get('how_stanford_affiliated')

    cme_user_profile.patient_population = post_vars.get('patient_population')

    if post_vars.get('specialty') == 'Other':
        cme_user_profile.specialty = post_vars.get('specialty_free')
    else:
        cme_user_profile.specialty = post_vars.get('specialty')

    if post_vars.get('sub_specialty') == 'Other':
        cme_user_profile.sub_specialty = post_vars.get('sub_specialty_free')
    else:
        cme_user_profile.sub_specialty = post_vars.get('sub_specialty')

    cme_user_profile.address_1 = post_vars.get('address_1')
    cme_user_profile.address_2 = post_vars.get('address_2')
    cme_user_profile.city = post_vars.get('city')
    cme_user_profile.state_province = post_vars.get('state_province')
    cme_user_profile.postal_code = post_vars.get('postal_code')
    cme_user_profile.country = post_vars.get('country')
    cme_user_profile.phone_number = post_vars.get('phone_number')
    cme_user_profile.extension = post_vars.get('extension')
    cme_user_profile.fax = post_vars.get('fax')

    if post_vars.get('hear_about_us') == 'Other':
        cme_user_profile.hear_about_us = post_vars.get('hear_about_us_free')
    else:
        cme_user_profile.hear_about_us = post_vars.get('hear_about_us')

    cme_user_profile.mailing_list = 1 if post_vars.get('mailing_list') == 'true' else 0

    try:
        cme_user_profile.save()

    except Exception:
        log.exception("UserProfile creation failed for user {0}.".format(user.email))
    return (user, cme_user_profile, registration)


def validate_required_fields(post_vars):
    """
    Checks that required free text fields contain at least 2 chars
    `post_vars` is dict of post parameters (a `dict`)
    Returns a dict indicating failure, field and message on empty field else None
    """

    #Add additional required fields here
    required_fields_list = [{'email': 'A properly formatted e-mail is required.'},
                            {'password': 'A valid password is required.'},
                            {'username': 'Username must be minimum of two characters long.'},
                            {'name': 'Your legal name must be a minimum of two characters long.'},
                            {'profession': 'Choose your profession.'},
                            {'license_number': 'Enter your license number.'},
                            {'patient_population': 'Choose your patient population'},
                            {'specialty': 'Choose your specialty'},
                            {'address_1': 'Enter your Address 01'},
                            {'city': 'Enter your city'},
                            {'state_province': 'Choose your state/Province'},
                            {'postal_code': 'Enter your postal code'},
                            {'country': 'Choose your country'},
                            {'phone_number': 'Enter your phone number'},
                            {'hear_about_us': 'Choose how you heard about us'}
                           ]

    error = {}
    for required_field in required_fields_list:
        for key, val in required_field.iteritems():   
            if len(post_vars.get(key)) < 2:
                error['success'] = False
                error['value'] = val
                error['field'] = key
                return error


def validate_required_boxes(post_vars):
    """
    Checks that required check boxes are checked
    `post_vars is dict of post parameters (a `dict)
    Returns a dict indicating failure, field and message on empty field else None
    """

    #Add additional required boxes here
    required_boxes_dict = {'terms_of_service': 'You must accept the terms of service.',
                           'honor_code': 'To enroll, you must follow the honor code.',
                           }

    error = {}
    for k, val in required_boxes_dict.items():
        if post_vars.get(k, 'false') != u'true':
            error['success'] = False
            error['value'] = val
            error['field'] = k
            return error


def validate_required_secondaries(post_vars):
    """
    Checks that required "secondary" text fields contain at least 2 chars. A secondary field is one that appears on the form if
    the user chooses a particular value in the corresponding primary. E.g. if "Other" chosen in sub_specialty then the
    sub_specialty_free secondary field pops up on the registration form.
    `post_vars is dict of post parameters (a `dict)
    Returns a dict indicating failure, field and message on empty field else None
    """

    #Add additional required secondaries here
    required_secondaries_dict = {'stanford_affiliated': ('1', 'how_stanford_affiliated', 'Choose how you are affiliated with Stanford.'),
                                 'how_stanford_affiliated': ('Other', 'how_stanford_affiliated_free', 'Enter how you are affiliated with Stanford.'),
                                 'specialty': ('Other', 'specialty_free', 'Enter your specialty.'),
                                 'sub_specialty': ('Other', 'sub_specialty_free', 'Enter your sub-specialty.'),
                                 'hear_about_us': ('Other', 'hear_about_us_free', 'Enter how you heard about us.')
                                 }

    error = {}
    for k, val in required_secondaries_dict.items():
        if post_vars.get(k) == val[0] and len(post_vars.get(val[1])) < 2:
            error['success'] = False
            error['value'] = val[2]
            error['field'] = k
            return error


def validate_required_radios(post_vars):
    """
    Checks that required radio buttons have been checked
    `post_vars is dict of post parameters (a `dict)
    Returns a dict indicating failure, field and message on empty field else None
    """

    #Add additional required radios here
    required_radios_dict = {'stanford_affiliated': 'Select whether, or not, you are affiliated with Stanford.'
                            }

    error = {}
    for k, val in required_radios_dict.items():
        if k not in post_vars:
            error['success'] = False
            error['value'] = val
            error['field'] = k
            return error


#Construct dicts for specialty and sub-specialty dropdowns
SPECIALTY_CHOICES = {}
SUB_SPECIALTY_CHOICES = {}

PATIENT_POPULATION_CHOICES = (('Adult', 'Adult'),
                              ('Pediatric', 'Pediatric'),
                              ('Both', 'Both (Adult/Pediatric)'))
SPECIALTY_CHOICES['Adult'] = (('Addiction_Medicine', 'Addiction Medicine'),
                              ('Allergy', 'Allergy'),
                              ('Anesthesiology', 'Anesthesiology'),
                              ('Cardiology', 'Cardiology'),
                              ('Complimentary_Medicine', 'Complimentary Medicine'),
                              ('Critical_Care_Medicine_&_ICU', 'Critical Care Medicine & ICU'),
                              ('Dentistry', 'Dentistry'),
                              ('Dermatology', 'Dermatology'),
                              ('Emergency_Medicine', 'Emergency Medicine'),
                              ('Endocrinology', 'Endocrinology'),
                              ('Family_Practice', 'Family Practice'),
                              ('Gastroenterology_&_Hepatology', 'Gastroenterology & Hepatology'),
                              ('General_Practice', 'General Practice'),
                              ('Gerontology', 'Gerontology'),
                              ('Head_&_Neck_Surgery', 'Head & Neck Surgery'),
                              ('Health_Education', 'Health Education'),
                              ('Hematology', 'Hematology'),
                              ('Immunology_&_Rheumatology', 'Immunology & Rheumatology'),
                              ('Infectious_Disease', 'Infectious Disease'),
                              ('Internal_Medicine', 'Internal Medicine'),
                              ('Nephrology', 'Nephrology'),
                              ('Neurology', 'Neurology'),
                              ('Neurosurgery', 'Neurosurgery'),
                              ('Nutrition', 'Nutrition'),
                              ('Obstetrics & Gynecology', 'Obstetrics & Gynecology'),
                              ('Oncology', 'Oncology'),
                              ('Ophthalmology', 'Ophthalmology'),
                              ('Orthopaedic_Surgery', 'Orthopaedic Surgery'),
                              ('Palliative_Care', 'Palliative Care'),
                              ('Pathology', 'Pathology'),
                              ('Pharmacology', 'Pharmacology'),
                              ('Physical_Medicine_&_Rehabilitation', 'Physical Medicine & Rehabilitation'),
                              ('Psychiatry', 'Psychiatry'),
                              ('Psychology', 'Psychology'),
                              ('Public_Health', 'Public Health'),
                              ('Pulmonology', 'Pulmonology'),
                              ('Radiology', 'Radiology'),
                              ('Radiation_Oncology', 'Radiation Oncology'),
                              ('Surgery', 'Surgery'),
                              ('Transplant', 'Transplant'),
                              ('Urology', 'Urology'))

SPECIALTY_CHOICES['Pediatric'] = (('Addiction_Medicine', 'Addiction Medicine'),
                                  ('Adolescent_Medicine', 'Adolescent Medicine'),
                                  ('Allergy', 'Allergy'),
                                  ('Anesthesiology', 'Anesthesiology'),
                                  ('Cardiology', 'Cardiology'),
                                  ('Complimentary_Medicine', 'Complimentary Medicine'),
                                  ('Critical_Care_Medicine_&_ICU', 'Critical Care Medicine & ICU'),
                                  ('Dentistry', 'Dentistry'),
                                  ('Dermatology', 'Dermatology'),
                                  ('Emergency_Medicine', 'Emergency Medicine'),
                                  ('Endocrinology', 'Endocrinology'),
                                  ('Family_Practice', 'Family Practice'),
                                  ('Gastroenterology_&_Hepatology', 'Gastroenterology & Hepatology'),
                                  ('General_Practice', 'General Practice'),
                                  ('Head_&_Neck_Surgery', 'Head & Neck Surgery'),
                                  ('Health_Education', 'Health Education'),
                                  ('Hematology', 'Hematology'),
                                  ('Immunology_&_Rheumatology', 'Immunology & Rheumatology'),
                                  ('Infectious_Disease', 'Infectious Disease'),
                                  ('Internal_Medicine', 'Internal Medicine'),
                                  ('Neonatology', 'Neonatology'),
                                  ('Nephrology', 'Nephrology'),
                                  ('Neurology', 'Neurology'),
                                  ('Neurosurgery', 'Neurosurgery'),
                                  ('Nutrition', 'Nutrition'),
                                  ('Obstetrics_&_Gynecology', 'Obstetrics & Gynecology'),
                                  ('Oncology', 'Oncology'),
                                  ('Ophthalmology', 'Ophthalmology'),
                                  ('Orthopaedic_Surgery', 'Orthopaedic Surgery'),
                                  ('Pathology', 'Pathology'),
                                  ('Pediatrics', 'Pediatrics'),
                                  ('Pharmacology', 'Pharmacology'),
                                  ('Physical_Medicine_&_Rehabilitation', 'Physical Medicine & Rehabilitation'),
                                  ('Psychiatry', 'Psychiatry'),
                                  ('Psychology', 'Psychology'),
                                  ('Public_Health', 'Public Health'),
                                  ('Pulmonology', 'Pulmonology'),
                                  ('Radiology', 'Radiology'),
                                  ('Radiation_Oncology', 'Radiation Oncology'),
                                  ('Surgery', 'Surgery'),
                                  ('Transplant', 'Transplant'),
                                  ('Urology', 'Urology'),
                                  ('Other', 'Other, please enter:'))

SPECIALTY_CHOICES['Both'] = (('Addiction_Medicine', 'Addiction Medicine'),
                             ('Adolescent_Medicine', 'Adolescent Medicine'),
                             ('Allergy', 'Allergy'),
                             ('Anesthesiology', 'Anesthesiology'),
                             ('Cardiology', 'Cardiology'),
                             ('Complimentary_Medicine', 'Complimentary Medicine'),
                             ('Critical_Care_Medicine_&_ICU', 'Critical Care Medicine & ICU'),
                             ('Dentistry', 'Dentistry'),
                             ('Dermatology', 'Dermatology'),
                             ('Emergency_Medicine', 'Emergency Medicine'),
                             ('Endocrinology', 'Endocrinology'),
                             ('Family_Practice', 'Family Practice'),
                             ('Gastroenterology_&_Hepatology', 'Gastroenterology & Hepatology'),
                             ('General_Practice', 'General Practice'),
                             ('Gerontology', 'Gerontology'),
                             ('Head_&_Neck_Surgery', 'Head & Neck Surgery'),
                             ('Health_Education', 'Health Education'),
                             ('Hematology', 'Hematology'),
                             ('Immunology_&_Rheumatology', 'Immunology & Rheumatology'),
                             ('Infectious_Disease', 'Infectious Disease'),
                             ('Internal_Medicine', 'Internal Medicine'),
                             ('Neonatology', 'Neonatology'),
                             ('Nephrology', 'Nephrology'),
                             ('Neurology', 'Neurology'),
                             ('Neurosurgery', 'Neurosurgery'),
                             ('Nutrition', 'Nutrition'),
                             ('Obstetrics_&_Gynecology', 'Obstetrics & Gynecology'),
                             ('Oncology', 'Oncology'),
                             ('Ophthalmology', 'Ophthalmology'),
                             ('Orthopaedic_Surgery', 'Orthopaedic Surgery'),
                             ('Palliative_Care', 'Palliative Care'),
                             ('Pathology', 'Pathology'),
                             ('Pediatrics', 'Pediatrics'),
                             ('Pharmacology', 'Pharmacology'),
                             ('Physical_Medicine_&_Rehabilitation', 'Physical Medicine & Rehabilitation'),
                             ('Psychiatry', 'Psychiatry'),
                             ('Psychology', 'Psychology'),
                             ('Public_Health', 'Public Health'),
                             ('Pulmonology', 'Pulmonology'),
                             ('Radiology', 'Radiology'),
                             ('Radiation_Oncology', 'Radiation Oncology'),
                             ('Surgery', 'Surgery'),
                             ('Transplant', 'Transplant'),
                             ('Urology', 'Urology'),
                             ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Cardiology'] = (('Cardiopulmonary', 'Cardiopulmonary'),
                                       ('Cardiothoracic', 'Cardiothoracic'),
                                       ('Cardiovascular_Disease', 'Cardiovascular Disease'),
                                       ('Cath_Angio_Lab', 'Cath Angio/Lab'),
                                       ('Electrophysiology', 'Electrophysiology'),
                                       ('Interventional_Cardiology', 'Interventional Cardiology'),
                                       ('Surgery', 'Surgery'),
                                       ('Vascular', 'Vascular'),
                                       ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Internal_Medicine'] = (('Cardiology', 'Cardiology'),
                                              ('Dermatology', 'Dermatology'),
                                              ('Endocrinology_Gerontology_&_Metabolism', 'Endocrinology, Gerontology & Metabolism'),
                                              ('Gastroenterology_&_Hepatology', 'Gastroenterology & Hepatology'),
                                              ('Hematology', 'Hematology'),
                                              ('Immunology_&_Rheumatology', 'Immunology & Rheumatology'),
                                              ('Infectious_Disease', 'Infectious Disease'),
                                              ('Nephrology', 'Nephrology'),
                                              ('Preventative_Medicine', 'Preventative Medicine'),
                                              ('Pulmonary', 'Pulmonary'),
                                              ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Obstetrics_Gynecology'] = (('Gynecology', 'Gynecology'),
                                                  ('Obstetrics', 'Obstetrics'),
                                                  ('Maternal_&_Fetal_Medicine', 'Maternal & Fetal Medicine'),
                                                  ('Women_Health', 'Women\'s Health'),
                                                  ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Oncology'] = (('Breast', 'Breast'),
                                     ('Gastroenterology', 'Gastroenterology'),
                                     ('Gynecology', 'Gynecology'),
                                     ('Hematology', 'Hematology'),
                                     ('Medical', 'Medical'),
                                     ('Radiation', 'Radiation'),
                                     ('Surgical', 'Surgical'),
                                     ('Urology', 'Urology'),
                                     ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Palliative_Care'] = (('Hospice', 'Hospice'),
                                            ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Pediatrics'] = (('Adolescent_Medicine', 'Adolescent Medicine'),
                                       ('Allergy', 'Allergy'),
                                       ('Anesthesiology', 'Anesthesiology'),
                                       ('Cardiac_Surgery', 'Cardiac Surgery'),
                                       ('Cardiology', 'Cardiology'),
                                       ('Critical_Care', 'Critical Care'),
                                       ('Dermatology', 'Dermatology'),
                                       ('Emergency', 'Emergency'),
                                       ('Endocrinology', 'Endocrinology'),
                                       ('Family Practice', 'Family Practice'),
                                       ('Gastroenterology', 'Gastroenterology'),
                                       ('Hematology_&_Oncology', 'Hematology & Oncology'),
                                       ('Immunology_&_Rheumatology', 'Immunology & Rheumatology'),
                                       ('Internal_Medicine', 'Internal Medicine'),
                                       ('Infectious_Disease', 'Infectious Disease'),
                                       ('Neonatology', 'Neonatology'),
                                       ('Nephrology', 'Nephrology'),
                                       ('Neurology', 'Neurology'),
                                       ('Obstetrics_&_Gynecology', 'Obstetrics & Gynecology'),
                                       ('Otolaryngology_Head_&_Neck', 'Otolaryngology/ Head & Neck'),
                                       ('Oncology', 'Oncology'),
                                       ('Ophthalmology', 'Ophthalmology'),
                                       ('Orthopaedic_Surgery', 'Orthopaedic Surgery'),
                                       ('Osteopathy', 'Osteopathy'),
                                       ('Pathology', 'Pathology'),
                                       ('Pediatric_Intensive_Care', 'Pediatric Intensive Care'),
                                       ('Psychiatry', 'Psychiatry'),
                                       ('Psychology', 'Psychology'),
                                       ('Pulmonary', 'Pulmonary'),
                                       ('Radiology', 'Radiology'),
                                       ('Surgery', 'Surgery'),
                                       ('Urology', 'Urology'),
                                       ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Pulmonology'] = (('Critical_Care', 'Critical Care'),
                                        ('Respiratory', 'Respiratory'),
                                        ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Surgery'] = (('Bariatric_Surgery', 'Bariatric Surgery'),
                                    ('Cardiac_Surgery', 'Cardiac Surgery'),
                                    ('Cardiothoracic_Surgery', 'Cardiothoracic Surgery'),
                                    ('Colon_&_Rectal_Surgery', 'Colon & Rectal Surgery'),
                                    ('Emergency_Medicine', 'Emergency Medicine'),
                                    ('Gastrointestinal_Surgery', 'Gastrointestinal Surgery'),
                                    ('Neurosurgery', 'Neurosurgery'),
                                    ('Oral_&_Maxillofacial_Surgery', 'Oral & Maxillofacial Surgery'),
                                    ('Orthopaedic_Surgery', 'Orthopaedic Surgery'),
                                    ('Plastic_&_Reconstructive_Surgery', 'Plastic & Reconstructive Surgery'),
                                    ('Surgical_Critical_Care', 'Surgical Critical Care'),
                                    ('Surgical_Oncology', 'Surgical Oncology'),
                                    ('Thoracic_Surgery', 'Thoracic Surgery'),
                                    ('Trauma_Surgery', 'Trauma Surgery'),
                                    ('Upper_Extremity_Hand_Surgery', 'Upper Extremity/ Hand Surgery'),
                                    ('Vascular_Surgery', 'Vascular Surgery'),
                                    ('Other', 'Other, please enter:'))

SUB_SPECIALTY_CHOICES['Transplant'] = (('Solid_Organ', 'Solid Organ'),
                                       ('Blood_and_Bone_Marrow', 'Blood and Bone Marrow'),
                                       ('Other', 'Other, please enter:'))
