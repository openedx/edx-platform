from django.core.mail import EmailMultiAlternatives, get_connection
from subprocess import Popen, PIPE
from celery import task
from django.conf import settings
from mitxmako.shortcuts import render_to_string
from django.contrib.auth.models import User, Group
from celery.task import current
from bulk_email.models import *

from courseware.access import get_access_group_name

import math
import time
import logging
log = logging.getLogger(__name__)

EMAILS_PER_WORKER=getattr(settings, 'EMAILS_PER_WORKER', 10)

@task()
def delegate_emails(hash_for_msg, recipient, course_id, course_title, course_url):
    '''
    Delegates emails by querying for the list of recipients who should
    get the mail, chopping up into batches of EMAILS_PER_WORKER size,
    and queueing up worker jobs.

    Recipient is {'students', 'staff', or 'all'}

    Returns the number of batches (workers) kicked off.
    '''
    if recipient == "students":
        recipient_qset = User.objects.filter(courseenrollment__course_id=course_id, is_staff=False).values('profile__name', 'email')
    elif recipient == "staff":
        recipient_qset = User.objects.filter(courseenrollment__course_id=course_id, is_staff=True).values('profile__name', 'email')
    else:
        recipient_qset = User.objects.filter(courseenrollment__course_id=course_id).values('profile__name', 'email')

    recipient_list = list(recipient_qset)
    total_num_emails = recipient_qset.count()
    num_workers=int(math.ceil(float(total_num_emails)/float(EMAILS_PER_WORKER)))
    chunk=int(math.ceil(float(total_num_emails)/float(num_workers)))

    for i in range(num_workers):
        to_list=recipient_list[i*chunk:i*chunk+chunk]
        course_email(hash_for_msg, to_list, course_title, course_url, False)
    return num_workers


@task(default_retry_delay=15, max_retries=5)
def course_email(hash_for_msg, to_list, course_title, course_url, throttle=False):
    """                                                                                                   
    Takes a subject and an html formatted email and sends it from
    sender to all addresses in the to_list, with each recipient
    being the only "to".  Emails are sent multipart, in both plain
    text and html.  
    """

    msg = CourseEmail.objects.get(hash=hash_for_msg)
    subject = "[" + course_title + "] " + msg.subject

    p = Popen(['lynx','-stdin','-display_charset=UTF-8','-assume_charset=UTF-8','-dump'], stdin=PIPE, stdout=PIPE)
    (plaintext, err_from_stderr) = p.communicate(input=msg.html_message.encode('utf-8')) #use lynx to get plaintext

    from_addr = settings.DEFAULT_BULK_FROM_EMAIL
    #TODO generate course-specific from address

    if err_from_stderr:
        log.info(err_from_stderr)

    try:
        connection = get_connection() #get mail connection from settings
        connection.open()
        num_sent = 0
        num_error = 0

        while to_list:
            (name, email) = to_list[-1]
            html_footer = render_to_string('emails/email_footer.html',
                                           {'name':name,
                                            'email':email,
                                            'course_title':course_title,
                                            'course_url':course_url})
            plain_footer = render_to_string('emails/email_footer.txt',
                                            {'name':name,
                                             'email':email,
                                             'course_title':course_title,
                                             'course_url':course_url})
    
            email_msg = EmailMultiAlternatives(subject, plaintext+plain_footer.encode('utf-8'), from_addr, [email], connection=connection)
            email_msg.attach_alternative(msg.html_message+html_footer.encode('utf-8'), 'text/html')

            if throttle or current.request.retries > 0: #throttle if we tried a few times and got the rate limiter
                time.sleep(0.2)

            try:
                connection.send_messages([email_msg])
                log.info('Email with hash ' + hash_for_msg + ' sent to ' + email)
                num_sent += 1
            except STMPDataError as exc:
                log.warn('Email with hash ' + hash_for_msg + ' not delivered to ' + email + ' due to error: ' + exc.smtp_error)
                num_error += 1
                connection.open() #reopen connection, in case.

            to_list.pop()

        connection.close()
        return "Sent %d, Fail %d" % (num_sent, num_error)

    except (SMTPDataError, SMTPConnectError, SMTPServerDisconnected) as exc:
        raise course_email.retry(arg=[hash_for_msg, to_list, course_title, course_url, current.request.retries>0], exc=exc, countdown=(2 ** current.request.retries)*15)
