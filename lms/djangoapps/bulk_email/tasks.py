from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from bulk_email.models import *

import math

EMAILS_PER_WORKER=getattr(settings, 'EMAILS_PER_WORKER', 10)

@task()
def delegate_emails(hash_for_msg, recipient, course):
    '''
    Delegates emails by querying for the list of recipients who should
    get the mail, chopping up into batches of EMAILS_PER_WORKER size,
    and queueing up worker jobs.

    Recipient is {'students', 'staff', or 'all'}

    Returns the number of batches (workers) kicked off.
    '''

    recipient_qset = User.objects.all()
    if recipient == "students":
        #get student list
        pass
    elif recipient == "staff":
        #get staff list
        pass
    else:
        #everyone
        pass
    recipient_list = list(recipient_qset)

    total_num_emails = recipient_qset.count()
    num_workers=int(math.ceil(float(total_num_emails)/float(EMAILS_PER_WORKER)))
    chunk=int(math.ceil(float(total_num_emails)/float(num_workers)))

    for i in range(num_workers):
        to_list=recipient_list[i*chunk:i*chunk+chunk]
        course_email.delay(hash_for_msg, to_list, False, course)
    return num_workers


@task(default_retry_delay=15, max_retries=5)
def course_email(hash_for_msg, to_list, course, throttle=False):
    """                                                                                                   
    Takes a subject and an html formatted email and sends it from
    sender to all addresses in the to_list, with each recipient
    being the only "to".  Emails are sent multipart, in both plain
    text and html.  
    """

    msg = CourseEmail.objects.get(hash=hash_for_msg)
