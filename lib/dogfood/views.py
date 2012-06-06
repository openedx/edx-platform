'''
dogfood.py

For using mitx / edX / i4x in checking itself.

df_capa_problem: accepts an XML file for a problem, and renders it.  
'''
import logging
import datetime
import re
import os	# FIXME - use OSFS instead

from fs.osfs import OSFS

from django.conf import settings
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.mail import send_mail
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string

import courseware.capa.calc
import track.views
from lxml import etree


from courseware.module_render import make_track_function, I4xSystem
from courseware.models import StudentModule
from multicourse import multicourse_settings
from student.models import UserProfile
from util.cache import cache
from util.views import accepts

import courseware.content_parser as content_parser
import courseware.modules

log = logging.getLogger("mitx.courseware")

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments = True))

DOGFOOD_COURSENAME = 'edx_dogfood'	# FIXME - should not be here; maybe in settings

def update_problem(pfn,pxml,coursename=None,overwrite=True,filestore=None):
    '''
    update problem with filename pfn, and content (xml) pxml.
    '''
    if not filestore:
        if not coursename: coursename = DOGFOOD_COURSENAME
        xp = multicourse_settings.get_course_xmlpath(coursename)	# path to XML for the course
        pfn2 = settings.DATA_DIR + xp + 'problems/%s.xml' % pfn
        fp = open(pfn2,'w')
    else:
        pfn2 = 'problems/%s.xml' % pfn
        fp = filestore.open(pfn2,'w')

    if os.path.exists(pfn2) and not overwrite: return		# don't overwrite if already exists and overwrite=False
    pxmls = pxml if type(pxml) in [str,unicode] else etree.tostring(pxml,pretty_print=True)
    fp.write(pxmls)
    fp.close()

def df_capa_problem(request, id=None):
    '''
    dogfood capa problem.

    Accepts XML for a problem, inserts it into the dogfood course.xml.
    Returns rendered problem.
    '''
    # "WARNING: UNDEPLOYABLE CODE. FOR DEV USE ONLY."
    
    if settings.DEBUG:
        print '[lib.dogfood.df_capa_problem] id=%s' % id

    if not 'coursename' in request.session:
        coursename = DOGFOOD_COURSENAME
    else:
        coursename = request.session['coursename']

    xp = multicourse_settings.get_course_xmlpath(coursename)	# path to XML for the course

    # Grab the XML corresponding to the request from course.xml
    module = 'problem'

    try:
        xml = content_parser.module_xml(request.user, module, 'id', id, coursename)
    except Exception,err:
        print "[lib.dogfood.df_capa_problem] error in calling content_parser: %s" % err
        xml = None

    # if problem of given ID does not exist, then create it
    # do this only if course.xml has a section named "DogfoodProblems"
    if not xml:
        m = re.match('filename([A-Za-z0-9_]+)$',id)	# extract problem filename from ID given
        if not m:
            raise Exception,'[lib.dogfood.df_capa_problem] Illegal problem id %s' % id
        pfn = m.group(1)
        print '[lib.dogfood.df_capa_problem] creating new problem pfn=%s' % pfn

        # add problem to course.xml
        fn = settings.DATA_DIR + xp + 'course.xml'
        xml = etree.parse(fn)
        seq = xml.find('chapter/section[@name="DogfoodProblems"]/sequential')	# assumes simplistic course.xml structure!
        if seq==None:
            raise Exception,"[lib.dogfood.views.df_capa_problem] missing DogfoodProblems section in course.xml!"
        newprob = etree.Element('problem')
        newprob.set('type','lecture')
        newprob.set('showanswer','attempted')
        newprob.set('rerandomize','never')
        newprob.set('title',pfn)
        newprob.set('filename',pfn)
        newprob.set('name',pfn)
        seq.append(newprob)
        fp = open(fn,'w')
        fp.write(etree.tostring(xml,pretty_print=True))	# write new XML
        fp.close()

        # now create new problem file
        # update_problem(pfn,'<problem>\n<text>\nThis is a new problem\n</text>\n</problem>\n',coursename,overwrite=False)
    
        # reset cache entry
        user = request.user
        groups = content_parser.user_groups(user)
        options = {'dev_content':settings.DEV_CONTENT, 
                   'groups' : groups}
        filename = xp + 'course.xml'
        cache_key = filename + "_processed?dev_content:" + str(options['dev_content']) + "&groups:" + str(sorted(groups))
        print '[lib.dogfood.df_capa_problem] cache_key = %s' % cache_key
        #cache.delete(cache_key)
        tree = content_parser.course_xml_process(xml)	# add ID tags
        cache.set(cache_key,etree.tostring(tree),60)
        # settings.DEFAULT_GROUPS.append('dev')	# force content_parser.course_file to not use cache

    xml = content_parser.module_xml(request.user, module, 'id', id, coursename)
    if not xml:
        print "[lib.dogfood.df_capa_problem] problem xml not found!"

    # add problem ID to list so that is_staff check can be bypassed
    request.session['dogfood_id'] = id

    # hand over to quickedit to do the rest
    return quickedit(request,id=id,qetemplate='dogfood.html',coursename=coursename)

def quickedit(request, id=None, qetemplate='quickedit.html',coursename=None):
    '''
    quick-edit capa problem.

    Maybe this should be moved into capa/views.py
    Or this should take a "module" argument, and the quickedit moved into capa_module.

    id is passed in from url resolution
    qetemplate is used by dogfood.views.dj_capa_problem, to override normal template
    '''
    print "WARNING: UNDEPLOYABLE CODE. FOR DEV USE ONLY."
    print "In deployed use, this will only edit on one server"
    print "We need a setting to disable for production where there is"
    print "a load balanacer"

    if not request.user.is_staff:
        if not ('dogfood_id' in request.session and request.session['dogfood_id']==id):
            return redirect('/')

    if id=='course.xml':
        return quickedit_git_reload(request)

    # get coursename if stored
    if not coursename:
        coursename = multicourse_settings.get_coursename_from_request(request)
    xp = multicourse_settings.get_course_xmlpath(coursename)	# path to XML for the course

    def get_lcp(coursename,id):
        # Grab the XML corresponding to the request from course.xml
        module = 'problem'
        xml = content_parser.module_xml(request.user, module, 'id', id, coursename)
    
        ajax_url = settings.MITX_ROOT_URL + '/modx/'+module+'/'+id+'/'
    
        # Create the module (instance of capa_module.Module)
        system = I4xSystem(track_function = make_track_function(request), 
                           render_function = None, 
                           ajax_url = ajax_url,
                           filestore = OSFS(settings.DATA_DIR + xp),
                           #role = 'staff' if request.user.is_staff else 'student',		# TODO: generalize this
                           )
        instance=courseware.modules.get_module_class(module)(system, 
                                                             xml, 
                                                             id,
                                                             state=None)

        # create empty student state for this problem, if not previously existing
        s = StudentModule.objects.filter(student=request.user, 
                                         module_id=id)
        if len(s) == 0 or s is None:
            smod=StudentModule(student=request.user, 
                               module_type = 'problem',
                               module_id=id, 
                               state=instance.get_state())
            smod.save()

        lcp = instance.lcp
        pxml = lcp.tree
        pxmls = etree.tostring(pxml,pretty_print=True)

        return instance, pxmls

    instance, pxmls = get_lcp(coursename,id)

    # if there was a POST, then process it
    msg = ''
    if 'qesubmit' in request.POST:
        action = request.POST['qesubmit']
        if "Revert" in action:
            msg = "Reverted to original"
        elif action=='Change Problem':
            key = 'quickedit_%s' % id
            if not key in request.POST:
                msg = "oops, missing code key=%s" % key
            else:
                newcode = request.POST[key]

                # see if code changed
                if str(newcode)==str(pxmls) or '<?xml version="1.0"?>\n'+str(newcode)==str(pxmls):
                    msg = "No changes"
                else:
                    # check new code
                    isok = False
                    try:
                        newxml = etree.fromstring(newcode)
                        isok = True
                    except Exception,err:
                        msg = "Failed to change problem: XML error \"<font color=red>%s</font>\"" % err
    
                    if isok:
                        filename = instance.lcp.fileobject.name
                        fp = open(filename,'w')		# TODO - replace with filestore call?
                        fp.write(newcode)
                        fp.close()
                        msg = "<font color=green>Problem changed!</font> (<tt>%s</tt>)"  % filename
                        instance, pxmls = get_lcp(coursename,id)

    lcp = instance.lcp

    # get the rendered problem HTML
    phtml = instance.get_problem_html()
    init_js = instance.get_init_js()
    destory_js = instance.get_destroy_js()

    context = {'id':id,
               'msg' : msg,
               'lcp' : lcp,
               'filename' : lcp.fileobject.name,
               'pxmls' : pxmls,
               'phtml' : phtml,
               "destroy_js":destory_js,
               'init_js':init_js, 
               'csrf':csrf(request)['csrf_token'],
               }

    result = render_to_response(qetemplate, context)
    return result

def quickedit_git_reload(request):
    '''
    reload course.xml and all courseware files for this course, from the git repo.
    assumes the git repo has already been setup.
    staff only.
    '''
    if not request.user.is_staff:
        return redirect('/')

    # get coursename if stored
    coursename = multicourse_settings.get_coursename_from_request(request)
    xp = multicourse_settings.get_course_xmlpath(coursename)	# path to XML for the course

    msg = ""
    if 'cancel' in request.POST:
        return redirect("/courseware")
        
    if 'gitupdate' in request.POST:
        import os			# FIXME - put at top?
        cmd = "cd ../data%s; git reset --hard HEAD; git pull origin %s" % (xp,xp.replace('/',''))
        msg += '<p>cmd: %s</p>' % cmd
        ret = os.popen(cmd).read()
        msg += '<p><pre>%s</pre></p>' % ret.replace('<','&lt;')
        msg += "<p>git update done!</p>"

    context = {'id':id,
               'msg' : msg,
               'coursename' : coursename,
               'csrf':csrf(request)['csrf_token'],
               }

    result = render_to_response("gitupdate.html", context)
    return result
