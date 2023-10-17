
from common.djangoapps.edxmako.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import PermissionDenied
from cms.djangoapps.contentstore.views.certificates import _get_course_and_check_access
from common.djangoapps.util.json_request import JsonResponse
from opaque_keys.edx.keys import  CourseKey
from common.djangoapps.edxmako.shortcuts import render_to_response
from cms.djangoapps.contentstore.views.item import create_item_import , _update_with_callback ,_save_xblock
import openpyxl
import tablib

@login_required
@ensure_csrf_cookie
def viewImportExcel (request, course_id) :
    course_key = CourseKey.from_string(course_id)
    try:
        course = _get_course_and_check_access(course_key, request.user)
    except PermissionDenied:
        msg = _('PermissionDenied: Failed in authenticating {user}').format(user=request.user)
        return JsonResponse({"error": msg}, status=403)
    context = {
          'context_course': course,
    }
    parts = course_id.split('+')
    organization = parts[0].split(":")[1]  
    course_number = parts[1]
    course_run = parts[2]
    parent_locator = f'block-v1:{organization}+{course_number}+{course_run}+type@course+block@course'
    if request.method == "POST" and request.FILES.get("excel_file"):
        excel_file = request.FILES["excel_file"]
   
        if excel_file.name.endswith('.xlsx'):
            dataset = tablib.Dataset()  
            dataImport = dataset.load(excel_file.read(), format='xlsx')    

            section=create_item_import(request, parent_locator, category='chapter', display_name='Mở đầu')
        #     # lesson= create_item_import(request, parent_locator=str(section.location) , category='sequential', display_name='Mở đầu') 
        #     # unit= create_item_import(request, parent_locator= str(lesson.location)  ,category='vertical', display_name='unit')  
        #     # html = create_item_import(request, parent_locator= str(unit.location)  ,category='html')  
           
            section_block = create_item_import(request ,parent_locator, category='chapter', display_name='Nội dung khoá học')
            list_video = []
            for data in dataImport:
                if data[1] is not None :
                    if ':' in data[1] :
                        
                        lesson_block =create_item_import(request, parent_locator=str(section_block.location) , category='sequential', display_name=data[1]) 
                        create_item_import(request, parent_locator=str(lesson_block.location), category='vertical', display_name='Mở đầu')
                        unit_block=create_item_import(request, parent_locator=str(lesson_block.location), category='vertical', display_name='Nội dung bài học')
                        html_block =create_item_import(request, parent_locator= str(unit_block.location) ,category='html')  
                    if data[3] is not None and 'video' in data[3].lower() and data[5] is not None:
                        videos =[]
                        videos.append(data[5])
                        list_video.append({'title' : data[2], 'video' : videos})
                        # _save_xblock(xblock=html_block , user=request.user, data=f'<p><a href="{data[5]}" title={data[2]}>video: {data[2]}</a></p>')
            url_video = ''
            for v in list_video :
      
                for e in v['video'] :
                    url_ = f'<p><a href="{e}" title={v["title"]}>Video: {v["title"]}</a></p>'
                    url_video += url_
            _save_xblock(xblock=html_block , user=request.user, data=url_video)

           
                  
    return render_to_response('import_excel.html', context)