import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from mailsnake import MailSnake

from student.models import UserProfile
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from courseware.grades import grade


BATCH_SIZE = 2000

log = logging.getLogger('edx.mailchimp')


class Command(BaseCommand):
    args = '<mailchimp_key mailchimp_list course_id>'
    help = 'Synchronizes a mailchimp list with the students of a course.'

    option_list = BaseCommand.option_list + (
        make_option('--key', action='store', help='mailchimp api key'),
        make_option('--list', action='store', dest='list_id', help='mailchimp list id'),
        make_option('--course', action='store', dest='course_id', help='xmodule course_id'),
        )

    def parse_options(self, options):
        if not options['key']:
            raise CommandError('missing key')

        if not options['list_id']:
            raise CommandError('missing list id')

        if not options['course_id']:
            raise CommandError('missing course id')

        return options['key'], options['list_id'], options['course_id']

    def handle(self, *args, **options):
        key, list_id, course_id = self.parse_options(options)

        log.info('Syncronizing email list for {0}'.format(course_id))

        mailchimp = connect_mailchimp(key, list_id, course_id)

        subscribed = get_subscribed(mailchimp, list_id)
        unsubscribed = get_unsubscribed(mailchimp, list_id)

        enrolled = get_enrolled_students(course_id)
        active = [s for s in enrolled if s.user.email not in unsubscribed]

        data = get_student_data(course_id, active)
        update_merge_tags(mailchimp, list_id, data)
        update_grade_data(mailchimp, list_id, data)

        enrolled_emails = set(s.user.email for s in enrolled)
        non_enrolled_emails = list(subscribed.difference(enrolled_emails))

        unsubscribe(mailchimp, list_id, non_enrolled_emails)


def connect_mailchimp(key, list_id, course_id):
    mailchimp = MailSnake(key)
    result = mailchimp.ping()
    log.debug(result)

    lists = mailchimp.lists(filters={'list_id': list_id})['data']

    if len(lists) != 1:
        raise CommandError('incorrect list id')

    list_name = lists[0]['name']

    log.debug('list name: %s' % list_name)

    # check that we are connecting to the correct list
    parts = course_id.replace('_', ' ').replace('/',' ').split()
    count = sum(1 for p in parts if p in list_name)
    if count != 4:
        log.debug(course_id)
        log.debug(list_name)
        raise CommandError('course_id does not match list name')

    return mailchimp


def get_student_data(course_id, students):
    store = modulestore()
    course_loc = CourseDescriptor.id_to_location(course_id)
    course = store.get_instance(course_id, course_loc)

    grades = []
    for student in students:
        student_email = student.user.email
        entry = {'EMAIL': student_email,
                 'FULLNAME': student.name.title()}

        # student_grade = grade(student.user, None, course)
        # for g in student_grade['section_breakdown']:
        #     name = g['label'].upper()
        #     entry[name] = g['percent']

        grades.append(entry)

    return grades


def get_enrolled_students(course_id):
    students = UserProfile.objects.filter(user__courseenrollment__course_id=course_id)
    return students


def get_unsubscribed(mailchimp, list_id):
    unsubscribed = mailchimp.listMembers(id=list_id, status='unsubscribed')
    return set(d['email'] for d in unsubscribed.get('data',[]))


def get_subscribed(mailchimp, list_id):
    unsubscribed = mailchimp.listMembers(id=list_id, status='subscribed')
    return set(d['email'] for d in unsubscribed.get('data',[]))


def unsubscribe(mailchimp, list_id, emails):
    result = mailchimp.listBatchUnsubscribe(id=list_id, emails=emails, send_goodbye=False, delete_member=False)
    log.debug(result)


def update_merge_tags(mailchimp, list_id, data):
    names = set()
    for row in data:
        names.update(row.keys())

    mc_vars = mailchimp.listMergeVars(id=list_id)
    mc_names = set(v['name'] for v in mc_vars)

    for name in names:
        tag = name_to_tag(name)

        # verify FULLNAME is present
        tags = [v['tag'] for v in mc_vars]
        if 'FULLNAME' not in tags:
            result = mailchimp.listMergeVarAdd(id=list_id,
                                               tag='FULLNAME',
                                               name='Full Name',
                                               options={'field_type':'text',
                                                        'public': False})
            log.debug(result)

        # add extra tags if not present
        if name not in mc_names and tag not in ['EMAIL', 'FULLNAME']:
            result = mailchimp.listMergeVarAdd(id=list_id,
                                               tag=tag,
                                               name=name,
                                               options={'field_type':'number',
                                                        'public': False})
            log.debug(result)


def update_grade_data(mailchimp, list_id, data):
    formated_data = list({name_to_tag(k):v for k, v in e.iteritems()} for e in data)

    # send the updates in batches of a fixed size
    for batch in batches(formated_data, BATCH_SIZE):
        result = mailchimp.listBatchSubscribe(id=list_id,
                                              batch=batch,
                                              double_optin=False,
                                              update_existing=True)
        log.debug(result)


def name_to_tag(name):
    return (name[:10] if len(name) > 10 else name).replace(' ','_').strip()


def batches(iterable, size):
    slices = range(0, len(iterable), size)
    return [iterable[slice(i, i + size)] for i in slices]
