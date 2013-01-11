import logging
import itertools
from optparse import make_option
from collections import namedtuple


from django.core.management.base import BaseCommand, CommandError

from mailsnake import MailSnake

from student.models import UserProfile, unique_id_for_user


BATCH_SIZE = 5000

log = logging.getLogger('edx.mailchimp')

FIELD_TYPES = {'UNIQUE_ID': 'text'}


class Command(BaseCommand):
    args = '<mailchimp_key mailchimp_list course_id>'
    help = 'Synchronizes a mailchimp list with the students of a course.'

    option_list = BaseCommand.option_list + (
        make_option('--key', action='store', help='mailchimp api key'),
        make_option('--list', action='store', dest='list_id',
                    help='mailchimp list id'),
        make_option('--course', action='store', dest='course_id',
                    help='xmodule course_id'),
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
        cleaned = get_cleaned(mailchimp, list_id)
        non_subscribed = unsubscribed.union(cleaned)

        enrolled = get_enrolled_students(course_id)
        active = enrolled.all().exclude(user__email__in=non_subscribed)

        data = get_student_data(course_id, active)

        update_merge_tags(mailchimp, list_id, data)
        update_data(mailchimp, list_id, data)

        enrolled_emails = set(enrolled.values_list('user__email', flat=True))
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
    parts = course_id.replace('_', ' ').replace('/', ' ').split()
    count = sum(1 for p in parts if p in list_name)
    if count != 4:
        log.info(course_id)
        log.info(list_name)
        raise CommandError('course_id does not match list name')

    return mailchimp


def get_student_data(course_id, students):
    # To speed the query, we won't retrieve the full User object, only
    # two of its values. The namedtuple simulates the User object.
    FakeUser = namedtuple('Fake', 'id username')

    def make(v):
        e = {'EMAIL': v['user__email'],
             'FULLNAME': v['name'].title()}

        e['UNIQUE_ID'] = unique_id_for_user(FakeUser(v['user_id'],
                                                     v['user__username']))
        return e

    fields = 'user__email', 'name', 'user_id', 'user__username'
    values = students.values(*fields)

    return [make(s) for s in values]


def get_enrolled_students(course_id):
    objects = UserProfile.objects
    students = objects.filter(user__courseenrollment__course_id=course_id)
    return students


def get_subscribed(mailchimp, list_id):
    return get_members(mailchimp, list_id, 'subscribed')


def get_unsubscribed(mailchimp, list_id):
    return get_members(mailchimp, list_id, 'unsubscribed')


def get_cleaned(mailchimp, list_id):
    return get_members(mailchimp, list_id, 'cleaned')


def get_members(mailchimp, list_id, status):
    mc_get_members = mailchimp.listMembers
    members = set()

    for page in itertools.count():
        response = mc_get_members(id=list_id,
                                  status=status,
                                  start=page,
                                  limit=BATCH_SIZE)
        data = response.get('data', [])

        if not data:
            break

        members.update(d['email'] for d in data)

    return members


def unsubscribe(mailchimp, list_id, emails):
    batch_unsubscribe = mailchimp.listBatchUnsubscribe
    result = batch_unsubscribe(id=list_id,
                               emails=emails,
                               send_goodbye=False,
                               delete_member=False)
    log.debug(result)


def update_merge_tags(mailchimp, list_id, data):
    names = set()
    for row in data:
        names.update(row.keys())

    mc_vars = mailchimp.listMergeVars(id=list_id)
    mc_names = set(v['name'] for v in mc_vars)

    mc_merge = mailchimp.listMergeVarAdd

    for name in names:
        tag = name_to_tag(name)

        # verify FULLNAME is present
        tags = [v['tag'] for v in mc_vars]
        if 'FULLNAME' not in tags:
            result = mc_merge(id=list_id,
                              tag='FULLNAME',
                              name='Full Name',
                              options={'field_type': 'text',
                                       'public': False})
            log.debug(result)

        # add extra tags if not present
        if name not in mc_names and tag not in ['EMAIL', 'FULLNAME']:
            ftype = FIELD_TYPES.get(name, 'number')
            result = mc_merge(id=list_id,
                              tag=tag,
                              name=name,
                              options={'field_type': ftype,
                                       'public': False})
            log.debug(result)


def update_data(mailchimp, list_id, data):
    format_entry = lambda e: {name_to_tag(k): v for k, v in e.iteritems()}
    formated_data = list(format_entry(e) for e in data)

    # send the updates in batches of a fixed size
    for batch in batches(formated_data, BATCH_SIZE):
        result = mailchimp.listBatchSubscribe(id=list_id,
                                              batch=batch,
                                              double_optin=False,
                                              update_existing=True)
        log.debug(result)


def name_to_tag(name):
    return (name[:10] if len(name) > 10 else name).replace(' ', '_').strip()


def batches(iterable, size):
    slices = range(0, len(iterable), size)
    return [iterable[slice(i, i + size)] for i in slices]
