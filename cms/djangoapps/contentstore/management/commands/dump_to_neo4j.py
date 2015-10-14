from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from py2neo import Graph, Node, Relationship, authenticate

def serialize_course(course):
    pass

class Command(BaseCommand):
    help = "Dump course items into a graph database"

    course_option = make_option(
        '--course',
        action='store',
        dest='course',
        default=False,
        help='--course <id> required, e.g. course-v1:org+course+run'
    )
    dump_all = make_option(
        '--all',
        action='store',
        dest='dump_all',
        default=False,
        help='dump all courses'
    )
    clear_all_first = make_option(
        '--clear-all-first',
        action='store',
        dest='clear_all_first',
        default=False,
        help='delete graph db before dumping'
    )

    option_list = BaseCommand.option_list + (course_option, dump_all, clear_all_first)

    def handle(self, *args, **options):
        graph = Graph(settings.NEO4J_URI)
        if options['clear_all_first']:
            print("deleting")
            graph.delete_all()
