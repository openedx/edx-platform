#!/usr/bin/python

from random import choice
import string
import traceback

from django.conf import settings
import courseware.capa.capa_problem as lcp
from dogfood.views import update_problem

def GenID(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])

randomid = GenID()

def check_problem_code(ans,the_lcp,correct_answers,false_answers):
    """
    ans = student's answer
    the_lcp = LoncapaProblem instance
    
    returns dict {'ok':is_ok,'msg': message with iframe}
    """
    pfn = "dog%s" % randomid
    pfn += the_lcp.problem_id.replace('filename','')    # add problem ID to dogfood problem name
    update_problem(pfn,ans,filestore=the_lcp.system.filestore)
    msg = '<hr width="100%"/>'
    msg += '<iframe src="%s/dogfood/filename%s" width="95%%" frameborder="1">No iframe support!</iframe>' % (settings.MITX_ROOT_URL,pfn)
    msg += '<hr width="100%"/>'

    is_ok = True
    try:
        # check correctness
        fp = the_lcp.system.filestore.open('problems/%s.xml' % pfn)
        test_lcp = lcp.LoncapaProblem(fp, '1', system=the_lcp.system)
    
        if not (test_lcp.grade_answers(correct_answers)['1_2_1']=='correct'):
            is_ok = False
        if (test_lcp.grade_answers(false_answers)['1_2_1']=='correct'):
            is_ok = False
    except Exception,err:
        is_ok = False
        msg += "<p>Error: %s</p>" % str(err).replace('<','&#60;')
        msg += "<p><pre>%s</pre></p>" % traceback.format_exc().replace('<','&#60;')
        
    ret = {'ok':is_ok,
           'msg': msg,
           }
    return ret
           
    
