import os.path

# THIS COMMAND IS OUT OF DATE

from lxml import etree

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

import xmodule

from xmodule.modulestore.django import modulestore
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module


def check_rendering(module):
    '''Check that all modules render'''
    all_ok = True
    print "Confirming all modules render. Nothing should print during this step. "

    def _check_module(module):
        try:
            module.get_html()
        except Exception as ex:
            print "==============> Error in ", module.id
            print ""
            print ex
            all_ok = False
        for child in module.get_children():
            _check_module(child)
    _check_module(module)
    print "Module render check finished"
    return all_ok


def check_sections(course):
    all_ok = True
    sections_dir = settings.DATA_DIR + "/sections"
    print "Checking that all sections exist and parse properly"
    if os.path.exists(sections_dir):
        print "Checking all section includes are valid XML"
        for f in os.listdir(sections_dir):
            sectionfile = sections_dir + '/' + f
            #print sectionfile
            # skip non-xml files:
            if not sectionfile.endswith('xml'):
                continue
            try:
                etree.parse(sectionfile)
            except Exception as ex:
                print "================> Error parsing ", sectionfile
                print ex
                all_ok = False
        print "checked all sections"
    else:
        print "Skipping check of include files -- no section includes dir (" + sections_dir + ")"
    return all_ok


class Command(BaseCommand):
    help = "Does basic validity tests on course.xml."

    def handle(self, *args, **options):
        all_ok = True

        # TODO (vshnayder): create dummy user objects.  Anon, authenticated, staff.
        # Check that everything works for each.
        # The objects probably shouldn't be actual django users to avoid unneeded
        # dependency on django.

        # TODO: use args as list of files to check.  Fix loading to work for other files.

        print "This command needs updating before use"
        return
"""
        sample_user = User.objects.all()[0]

        print "Attempting to load courseware"

        # TODO (cpennington): Get coursename in a legitimate way
        course_location = 'i4x://edx/6002xs12/course/6.002_Spring_2012'
        student_module_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_id,
            sample_user, modulestore().get_item(course_location))
        course = get_module(sample_user, None, course_location, student_module_cache)

        to_run = [
            #TODO (vshnayder) : make check_rendering work (use module_render.py),
            # turn it on
            check_rendering,
            check_sections,
        ]
        for check in to_run:
            all_ok = check(course) and all_ok

        # TODO: print "Checking course properly annotated with preprocess.py"

        if all_ok:
            print 'Courseware passes all checks!'
        else:
            print "Courseware fails some checks"
"""
