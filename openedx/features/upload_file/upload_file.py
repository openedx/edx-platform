from .forms import UploadFileForm
from .models import UploadFile
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import datetime
def index (request , course_id, usage_id) :

    post_data = request.POST.copy()  
    post_data['course_id'] = course_id
    post_data['block_id'] = usage_id
    post_data['email'] = request.user.email
    form = UploadFileForm(post_data, request.FILES)

    url_lms = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    if form.is_valid():
        uploadFile = UploadFile()
        uploadFile.email = form.cleaned_data['email']
        uploadFile.course_id = form.cleaned_data['course_id']
        uploadFile.block_id = form.cleaned_data['block_id']
        uploadFile.type = form.cleaned_data['type']
        uploadFile.file = request.FILES.get('file','')

        uploadFile.save()
        current_date = datetime.datetime.now()
        data = {
            "url" : url_lms + '/media/' + uploadFile.file.name,
            "date": current_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        return data
    else:
        errors = form.errors
        for field_name, error_list in errors.items():
            for error in error_list:
                print(f"Field: {field_name}, Error: {error}")
    return True

def getFileUser (block_id , email):
    file  = UploadFile.objects.filter( block_id=block_id, email=email)
    url_lms = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    data = {
        "url" : ''
    }
    
    if len(file) > 0:
        data = {
            "url" : url_lms + '/media/' + file[0].file.name,
            "date" : file[0].date
        }
    

    return data 