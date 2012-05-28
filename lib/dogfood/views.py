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

from courseware.module_render import render_module, make_track_function, I4xSystem
from multicourse import multicourse_settings
from util.cache import cache

import courseware.content_parser as content_parser
import courseware.modules
from courseware.views import quickedit

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
    print "WARNING: UNDEPLOYABLE CODE. FOR DEV USE ONLY."
    print "In deployed use, this will only edit on one server"
    print "We need a setting to disable for production where there is"
    print "a load balanacer"
    
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

    # hand over to quickedit to do the rest
    try:
        html = quickedit(request,id=id,qetemplate='dogfood.html',coursename=coursename)
        return html
    except Exception, err:
        print '[lib.dogfood.df_capa_problem] Error generating html on first pass: %s' % err
        
    return quickedit(request,id=id,qetemplate='dogfood.html',coursename=coursename)
