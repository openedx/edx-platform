"""
Script for finding all courses whose org/name pairs == other courses when ignoring case
"""
from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum


#
# To run from command line: ./manage.py cms --settings dev course_id_clash
#
class Command(BaseCommand):
    """
    Script for finding all courses in the Mongo Modulestore whose org/name pairs == other courses when ignoring case
    """
    help = 'List all courses ids in the Mongo Modulestore which may collide when ignoring case'

    def handle(self, *args, **options):
        mstore = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)  # pylint: disable=protected-access
        if hasattr(mstore, 'collection'):
            map_fn = '''
                function () {
                    emit(this._id.org.toLowerCase()+this._id.course.toLowerCase(), {target: this._id});
                }
            '''
            reduce_fn = '''
                function (idpair, matches) {
                    var result = {target: []};
                    matches.forEach(function (match) {
                        result.target.push(match.target);
                    });
                    return result;
                }
            '''
            finalize = '''
                function(key, reduced) {
                    if (Array.isArray(reduced.target)) {
                        return reduced;
                    }
                    else {return null;}
                    }
            '''
            results = mstore.collection.map_reduce(
                map_fn, reduce_fn, {'inline': True}, query={'_id.category': 'course'}, finalize=finalize
            )
            results = results.get('results')
            for entry in results:
                if entry.get('value') is not None:
                    print '{:-^40}'.format(entry.get('_id'))
                    for course_id in entry.get('value').get('target'):
                        print '   {}/{}/{}'.format(course_id.get('org'), course_id.get('course'), course_id.get('name'))

