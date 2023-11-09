from .forms import UploadFileForm
from .models import UploadFile
def index (request , course_id, usage_id) :

    post_data = request.POST.copy()  
    post_data['course_id'] = course_id
    post_data['block_id'] = usage_id
    post_data['email'] = request.user.email
    form = UploadFileForm(post_data, request.FILES)
    
    if form.is_valid():
        uploadFile = UploadFile()
        uploadFile.email = form.cleaned_data['email']
        uploadFile.course_id = form.cleaned_data['course_id']
        uploadFile.block_id = form.cleaned_data['block_id']
        uploadFile.type = form.cleaned_data['type']
        uploadFile.file = request.FILES.get('file','')
        print('===email========', form.cleaned_data['email'])
        print('======course_id=====', form.cleaned_data['course_id'])
        print('====block_id=======', form.cleaned_data['block_id'])
        print('=====file======', request.FILES.get('file',''))
        print('======type=========', form.cleaned_data['type'])
        uploadFile.save()
    else:
        errors = form.errors
        for field_name, error_list in errors.items():
            for error in error_list:
                print(f"Field: {field_name}, Error: {error}")
    return True