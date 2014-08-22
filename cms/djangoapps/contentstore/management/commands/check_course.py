from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import check_module_metadata_editability
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    help = '''Enumerates through the course and find common errors'''

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("check_course requires one argument: <course_id>")

        try:
            course_key = CourseKey.from_string(args[0])
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(args[0])

        store = modulestore()

        course = store.get_course(course_key, depth=3)

        err_cnt = 0

        def _xlint_metadata(module):
            err_cnt = check_module_metadata_editability(module)
            for child in module.get_children():
                err_cnt = err_cnt + _xlint_metadata(child)
            return err_cnt

        err_cnt = err_cnt + _xlint_metadata(course)

        # we've had a bug where the xml_attributes field can we rewritten as a string rather than a dict
        def _check_xml_attributes_field(module):
            err_cnt = 0
            if hasattr(module, 'xml_attributes') and isinstance(module.xml_attributes, basestring):
                print 'module = {0} has xml_attributes as a string. It should be a dict'.format(module.location)
                err_cnt = err_cnt + 1
            for child in module.get_children():
                err_cnt = err_cnt + _check_xml_attributes_field(child)
            return err_cnt

        err_cnt = err_cnt + _check_xml_attributes_field(course)

        # check for dangling discussion items, this can cause errors in the forums
        def _get_discussion_items(module):
            discussion_items = []
            if module.location.category == 'discussion':
                discussion_items = discussion_items + [module.location]

            for child in module.get_children():
                discussion_items = discussion_items + _get_discussion_items(child)

            return discussion_items

        discussion_items = _get_discussion_items(course)

        # now query all discussion items via get_items() and compare with the tree-traversal
        queried_discussion_items = store.get_items(course_key=course_key, qualifiers={'category': 'discussion'})

        for item in queried_discussion_items:
            if item.location not in discussion_items:
                print 'Found dangling discussion module = {0}'.format(item.location)
