import os
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
            # Save the uploaded file to the default storage
            file_name = default_storage.save(file_obj.name, file_obj)

            # Determine the file URL based on the storage backend
            storage_backend = default_storage.__class__.__name__
            if 'S3Boto3Storage' in storage_backend:
                # File URL for S3
                file_url = os.path.join(settings.AWS_S3_CUSTOM_DOMAIN, file_name)
            else:
                # File URL for local storage
                file_url = request.build_absolute_uri(settings.MEDIA_URL + file_name)

            return JsonResponse({'status': 'File uploaded', 'file_url': file_url})

        else:
            return JsonResponse({'status': 'No file uploaded'}, status=400)
