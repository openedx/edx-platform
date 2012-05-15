import os.path

from lxml import etree

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from courseware.content_parser import course_file
import courseware.module_render
import courseware.modules

class Command(BaseCommand):
    help = "Does basic validity tests on course.xml."
    def handle(self, *args, **options):
        check = True
        sample_user = User.objects.all()[0]
        print "Attempting to load courseware"
        course = course_file(sample_user)
        print "Confirming all problems have alphanumeric names"
        for problem in course.xpath('//problem'):
            filename = problem.get('filename')
            if not filename.isalnum():
                print "==============> Invalid (non-alphanumeric) filename", filename
                check = False
        print "Confirming all modules render. Nothing should print during this step. "
        for module in course.xpath('//problem|//html|//video|//vertical|//sequential|/tab'):
            module_class = courseware.modules.modx_modules[module.tag]
            # TODO: Abstract this out in render_module.py
            try: 
                module_class(etree.tostring(module), 
                             module.get('id'), 
                             ajax_url='',
                             state=None, 
                             track_function = lambda x,y,z:None, 
                             render_function = lambda x: {'content':'','destroy_js':'','init_js':'','type':'video'})
            except:
                print "==============> Error in ", etree.tostring(module)
                check = False
        print "Module render check finished"
        sections_dir = settings.DATA_DIR+"sections"
        if os.path.exists(sections_dir):
            print "Checking all section includes are valid XML"
            for f in os.listdir(sections_dir):
                print f
                etree.parse(sections_dir+'/'+f)
        else:
            print "Skipping check of include files -- no section includes dir ("+sections_dir+")"
        # TODO: print "Checking course properly annotated with preprocess.py"
        
            
        if check:
            print 'Courseware passes all checks!'
        else: 
            print "Courseware fails some checks"
