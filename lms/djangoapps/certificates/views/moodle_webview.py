import datetime
from microsite_configuration import microsite
from edxmako.shortcuts import render_to_response, marketing_link
from certificates.models import MdlCertificateIssued
from student.models import MdlToEdx

from django.contrib.auth.models import User
from django.conf import settings


def convert_timestamp_to_date(timestamp):
    return datetime.datetime.fromtimestamp(int(timestamp)).strftime('%B %d, %Y')

def render_moodle_html_view(request, moodle_cert_code, time_created, cert_date):
    """
    This public view generates an HTML representation of the specified user and course
    If a certificate is not available, we display a "Sorry!" screen instead
    """

    platform_name = microsite.get_value("platform_name", settings.PLATFORM_NAME)
    company_tos_url = marketing_link('LEGAL')
    company_about_url = marketing_link('ABOUT')
    course_id = ""

    context = common_context_content(platform_name, company_tos_url, company_about_url, course_id)

    if MdlCertificateIssued.objects.filter(code=moodle_cert_code, timecreated=time_created, certdate=cert_date).exists():
        context.update(valid_context_content(moodle_cert_code, platform_name, company_tos_url, company_about_url, course_id, time_created, cert_date))
        return render_to_response("certificates/valid.html", context)

    else:
        context.update(invalid_context_content())
        return render_to_response("certificates/invalid.html", context)

def common_context_content(platform_name, company_tos_url, company_about_url, course_id):

    context = {
        u'accomplishment_class_append': u'accomplishment-certificate',
        'company_about_title': u'About %s' %(platform_name),
        'company_contact_urltext': u'Contact %s' %(platform_name),
        'course_id': course_id,
        'company_about_urltext': u'Learn more about %s' %(platform_name),
        'certificate_verify_title': u'How %s Validates Student Certificates' %(platform_name),
        'company_careers_urltext': u'Work at %s' %(platform_name),
        'company_tos_urltext': u'Terms of Service &amp; Honor Code',
        u'logo_src': u'/static/images/bdu-logo.svg',
        'company_courselist_urltext': u'Learn with %s' %(platform_name),
        'company_about_description': u"An IBM community initiative, %s is the world's best education on big data. Learn about big data, data science and analytic technologies from experts using hands-on exercises and interactive videos. Best of all, it's completely free." %(platform_name),
        'certificate_verify_urltext': u'Validate this certificate for yourself',
        'copyright_text': u'&copy; 2015 %s. All rights reserved.' %(platform_name),
        'logo_subtitle': u'Certificate Validation',
        u'logo_url': u'/',
        'accomplishment_copy_about': u'About %s Accomplishments' %(platform_name),
        'certificate_verify_description': u'Certificates issued by %s are signed by a gpg key so that they can be validated independently by anyone with the %s public key. For independent verification, %s uses what is called a "detached signature"&quot;".' %(platform_name, platform_name, platform_name),
        'certificate_id_number_title': u'Certificate ID Number',
        u'company_privacy_url': company_tos_url,
        'document_banner': u'%s acknowledges the following student accomplishment' %(platform_name),
        'certificate_date_issued_title': u'Issued On:',
        u'company_tos_url': company_tos_url,
        u'company_verified_certificate_url': u'https://andela-dev.bigdatauniversity.com/verified-certificate',
        'company_privacy_urltext': u'Privacy Policy',
        'certificate_info_title': u'About %s Certificates' %(platform_name),
        'platform_name': platform_name,
        u'company_about_url': company_about_url
    }
    return context

def invalid_context_content():

    context = {
        'document_title': u'Invalid Certificate'
    }
    return context


def valid_context_content(moodle_cert_code, platform_name, company_tos_url, company_about_url, course_id, time_created, cert_date):

    certificate_user = MdlCertificateIssued.objects.get(code=moodle_cert_code, timecreated=time_created, certdate=cert_date)
    student_name = certificate_user.studentname
    course_name = certificate_user.classname
    facebook_app_id = microsite.get_value("FACEBOOK_APP_ID", settings.FACEBOOK_APP_ID)
    accomplishment_user_id = MdlToEdx.objects.get(mdl_user_id=certificate_user.mdl_userid).user_id
    accomplishment_copy_username = User.objects.get(id=accomplishment_user_id).username
    certificate_date_issued = convert_timestamp_to_date(certificate_user.certdate)
    certificate_id_number = moodle_cert_code

    context = {
        'accomplishment_banner_congrats': u"Congratulations! This page summarizes all of the details of what you've accomplished. Show it off to family, friends, and colleagues in your social and professional networks.",
        'accomplishment_copy_description_full': u'successfully completed, received a passing grade, and was awarded a %s Honor Code Certificate of Completion in ' %(platform_name),
        'badge': None,
        'certificate_verify_url': 'None%sNone' %(moodle_cert_code),
        'accomplishment_copy_course_description': u'a course of study offered by %s, through %s.' %(platform_name, platform_name),
        'accomplishment_copy_name': student_name,
        'share_url': 'https://andela-dev.bigdatauniversity.com/certificates/moodle/%s' %(certificate_id_number),
        'course_mode': u'honor',
        'accomplishment_banner_opening': u"%s, you've earned a certificate!" %(student_name),
        'accomplishment_copy_more_about': u"More about %s 's accomplishment"%(student_name),
        'facebook_share_text': u'I completed the %s course on %s' %(course_name, platform_name),
        'facebook_app_id': facebook_app_id,
        'organization_short_name': platform_name,
        'full_course_image_url': u'/static/images/bdu-logo.svg',
        'accomplishment_copy_course_org': platform_name,
        'certificate_type_description': u"An Honor Code Certificate signifies that an %s learner has agreed to abide by %s's honor code and completed all of the required tasks for this course under its guidelines." %(platform_name, platform_name),
        u'logo_src': u'/static/images/bdu-logo.svg',
        u'certificate_type': u'Honor Code',
        'company_about_description': u"An IBM community initiative, %s is the world's best education on big data. Learn about big data, data science and analytic technologies from experts using hands-on exercises and interactive videos. Best of all, it's completely free." %(platform_name),
        'course_number': course_id,
        'username': accomplishment_copy_username,
        'document_meta_description': u'This is a valid %s certificate for %s, who participated in %s' %(platform_name, student_name, course_name),
        'certificate_info_description': u"%s acknowledges achievements through certificates, which are awarded for various activities %s students complete under the <a href='%s'>%s Honor Code</a>.  Some certificates require completing additional steps, such as <a href='http://www.example.com/verified-certificate'> verifying your identity</a>." %(platform_name, platform_name, company_tos_url, platform_name),
        'linked_in_url': None,
        'twitter_url': 'https://twitter.com/intent/tweet?text=I completed a course on Big Data University. Take a look at my certificate.&url=http%3A%2F%2Fandela-dev.bigdatauniversity.com%2Fcertificates%2Fd896298e49504a8e951bc5edbd8fc22a',
        'organization_logo': None,
        'accomplishment_copy_course_name': course_name,
        'twitter_share_text': u'I completed a course on %s. Take a look at my certificate.' %(platform_name),
        'organization_long_name': None,
        'facebook_share_enabled': True,
        'accomplishment_copy_username': accomplishment_copy_username,
        'certificate_date_issued': certificate_date_issued,
        'certificate_data': {u'course_title': u'', u'name': u'Name of the certificate', u'is_active': True, u'signatories': [{u'name': u'', u'certificate': None, u'title': u'', u'organization': u'', u'signature_image_path': u'', u'id': 855336706}], u'version': 1, u'editing': False, u'id': 1376752691, u'description': u'Description of the certificate'},
        'document_title': u'%s Certificate | %s' %(platform_name, platform_name),
        'accomplishment_user_id': accomplishment_user_id,
        'accomplishment_more_title': u"More Information About %s's Certificate:" %(student_name),
        'certificate_id_number': certificate_id_number,
        'twitter_share_enabled': True,
        u'certificate_title': u'Certificate of Achievement',
    }

    # FINALLY, render appropriate certificate
    return context
