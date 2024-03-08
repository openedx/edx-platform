from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def file_upload_view(request):
    if request.method == 'POST':
        file_obj = request.FILES.get('file', None)
        if file_obj:
            # Save the uploaded file
            file_name = default_storage.save(file_obj.name, file_obj)

            # Construct the file's URL
            file_url = request.build_absolute_uri(settings.MEDIA_URL + file_name)

            return JsonResponse({'status': 'File uploaded', 'file_url': file_url})

        else:
            return JsonResponse({'status': 'No file uploaded'}, status=400)
