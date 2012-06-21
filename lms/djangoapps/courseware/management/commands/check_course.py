import os.path

from lxml import etree

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from courseware.content_parser import course_file
import courseware.module_render
import xmodule

import mitxmako.middleware as middleware
middleware.MakoMiddleware()

def check_names(user, course):
    '''
    Complain if any problems have alphanumeric names.
    TODO (vshnayder): there are some in 6.002x that don't.  Is that actually a problem?
    '''
    all_ok = True
    print "Confirming all problems have alphanumeric names"
    for problem in course.xpath('//problem'):
        filename = problem.get('filename')
        if not filename.isalnum():
            print "==============> Invalid (non-alphanumeric) filename", filename
            all_ok = False
    return all_ok

def check_rendering(user, course):
    '''Check that all modules render'''
    all_ok = True
    print "Confirming all modules render. Nothing should print during this step. "
    for module in course.xpath('//problem|//html|//video|//vertical|//sequential|/tab'):
        module_class = xmodule.modx_modules[module.tag]
        # TODO: Abstract this out in render_module.py
        try: 
            module_class(etree.tostring(module), 
                         module.get('id'), 
                         ajax_url='',
                         state=None, 
                         track_function = lambda x,y,z:None, 
                         render_function = lambda x: {'content':'','type':'video'})
        except Exception as ex:
            print "==============> Error in ", etree.tostring(module)
            print ""
            print ex
            all_ok = False
    print "Module render check finished"
    return all_ok

def check_sections(user, course):
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
        print "Skipping check of include files -- no section includes dir ("+sections_dir+")"
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

        sample_user = User.objects.all()[0]

        
        print "Attempting to load courseware"
        course = course_file(sample_user)

        to_run = [check_names,
                  # TODO (vshnayder) : make check_rendering work (use module_render.py),
                  # turn it on
                  #                  check_rendering,
                  check_sections,
                  ]
        for check in to_run:
            all_ok = check(sample_user, course) and all_ok

        # TODO: print "Checking course properly annotated with preprocess.py"
        
        if all_ok:
            print 'Courseware passes all checks!'
        else: 
            print "Courseware fails some checks"
