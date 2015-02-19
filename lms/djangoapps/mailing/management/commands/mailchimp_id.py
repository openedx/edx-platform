import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from mailsnake import MailSnake


class Command(BaseCommand):
    args = '<mailchimp_key web_id>'
    help = 'Get the list id from a web_id'

    option_list = BaseCommand.option_list + (
        make_option('--key', action='store', help='mailchimp api key'),
        make_option('--webid', action='store', dest='web_id', type=int,
                    help='mailchimp list web id'),
    )

    def parse_options(self, options):
        if not options['key']:
            raise CommandError('missing key')

        if not options['web_id']:
            raise CommandError('missing list web id')

        return options['key'], options['web_id']

    def handle(self, *args, **options):
        key, web_id = self.parse_options(options)

        mailchimp = MailSnake(key)

        lists = mailchimp.lists()['data']
        by_web_id = {l['web_id']: l for l in lists}

        list_with_id = by_web_id.get(web_id, None)

        if list_with_id:
            print "id: {} for web_id: {}".format(list_with_id['id'], web_id)
            print "list name: {}".format(list_with_id['name'])
        else:
            print "list with web_id: {} not found.".format(web_id)
            sys.exit(1)
