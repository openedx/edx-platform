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

        mailchimp = connect_mailchimp(key, list_id, course_id)

        unsubscribed = get_unsubscribed(mailchimp, list_id)
        data = get_grade_data(course_id, unsubscribed)

        update_merge_tags(mailchimp, list_id, data)
        update_grade_data(mailchimp, list_id, data)


def connect_mailchimp(key, web_id, course_id):
    mailchimp = MailSnake(key)
    result = mailchimp.ping()
    log.debug(result)

    lists = mailchimp.lists(filters={'list_id': web_id})['data']

    if len(lists) != 1:
        raise CommandError('incorrect list id')

    list_id = lists[0]['id']
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


def get_grade_data(course_id, emails_to_skip=None):
    emails_to_skip = emails_to_skip or []

    store = modulestore()
    course_loc = CourseDescriptor.id_to_location(course_id)
    course = store.get_instance(course_id, course_loc)

    students = UserProfile.objects.filter(user__courseenrollment__course_id=course_id)

    grades = []
    for student in students:
        student_email = student.user.email
        if student_email not in emails_to_skip:
            entry = {'EMAIL': student_email,
                     'FULLNAME': student.name.title()}

            # student_grade = grade(student.user, None, course)
            # for g in student_grade['section_breakdown']:
            #     name = g['label'].upper()
            #     entry[name] = g['percent']

            grades.append(entry)

    return grades


def get_unsubscribed(mailchimp, list_id):
    unsubscribed = mailchimp.listMembers(id=list_id, status='unsubscribed')
    return set(d['email'] for d in unsubscribed.get('data',[]))


def update_merge_tags(mailchimp, list_id, data):
    names = set()
    for row in data:
        names.update(row.keys())

    mc_vars = mailchimp.listMergeVars(id=list_id)
    mc_names = set(v['name'] for v in mc_vars)

    for name in names:
        tag = name_to_tag(name)
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
