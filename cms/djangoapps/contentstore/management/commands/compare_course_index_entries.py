import logging
from xmodule.modulestore.split_mongo.mongo_connection import MongoPersistenceBackend, DjangoFlexPersistenceBackend
from xmodule.modulestore.django import modulestore
from django.core.management.base import BaseCommand

from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    """
    A Command to determine if the Mongo active_versions and Django course_index tables are out of sync with one another.
    """

    def handle(self, *args, **options):
        module_store = modulestore()
        courses = module_store.get_courses()
        course_ids = [x.id for x in courses]
        out_of_sync = {}

        mongostore = MongoPersistenceBackend(**settings.CONTENTSTORE['DOC_STORE_CONFIG'])
        msqlstore = DjangoFlexPersistenceBackend(**settings.CONTENTSTORE['DOC_STORE_CONFIG'])

        def compare_entries(mongo_entry, msql_entry, course_id):
            draft = False
            published = False
            if(mongo_entry["draft-branch"] != msql_entry["draft-branch"]):
                draft = True
            if(mongo_entry["published-branch"] != msql_entry["published-branch"]):
                published = True
            if (draft | published):
                out_of_sync[course_id._to_string()] = (draft, published)
            return

        for course_id in course_ids:
            mongo_entry = mongostore.get_course_index(key=course_id)['versions']
            msql_entry = msqlstore.get_course_index(key=course_id)['versions']
            compare_entries(mongo_entry, msql_entry, course_id)

        print(out_of_sync)

        for course in out_of_sync:
            print(f'id: {course} is out of Sync in Draft:{out_of_sync[course][0]} in Published: {out_of_sync[course][1]}')
        print(f'The number of out-of-sync courses is : {len(out_of_sync)}')