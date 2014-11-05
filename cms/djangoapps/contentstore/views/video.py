"""
Views related to the video upload feature
"""

from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore
from util.json_request import expect_json, JsonResponse
from .access import has_course_access

from boto.s3.connection import S3Connection
from boto.s3.key import Key

__all__ = ['video_upload_handler']


@expect_json
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
def video_upload_handler(request, course_key_string):
    """
    The restful handler for video uploads.

    GET
        json: return json representing the videos that have been uploaded and their statuses
    PUT or POST
        json: upload a set of videos
    """
    # The feature flag should be enabled
    assert settings.FEATURES['ENABLE_VIDEO_UPLOAD_PIPELINE']

    course_key = CourseKey.from_string(course_key_string)

    # For now, assume all studio users that have access to the course can upload videos.
    # In the future, we plan to add a new org-level role for video uploaders.
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    # Check whether the video upload feature is configured for this course
    course = modulestore().get_course(course_key)
    if (
        course.video_upload_pipeline is None or
        not course.video_upload_pipeline.has_attr('Institute_Name') or
        not course.video_upload_pipeline.has_attr('Access_Token')
    ):
        return JsonResponse({"error": "Course not configured properly for video upload."}, status=400)

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            return video_upload_index(course, request)
        else:
            return video_upload_post(course, request)

    return HttpResponseNotFound()


def video_upload_index(course, request):
    """
    Returns a JSON in the following format: {
        videos: [
           {
              edx-video-id: xxx,
              file-name: xxx,
              date-uploaded: xxx,
              status: xxx,
           },
           ...
        ]
    }
    """
    pass


def video_upload_post(course, request):
    """
    Input (JSON): {
        files: [
            { file_name: xxx },
            ...
        ]
    }
    Returns (JSON): {
        files: [
            { file-name: xxx, upload-url: xxx },
            ...
        ]
    }
    """
    file_upload_urls = {}
    bucket = storage_service_bucket()
    institute_name = course.video_upload_pipeline['Institute_Name']

    for file in request.json['files']:
        # 1. generate edx_video_id
        edx_video_id = generate_edx_video_id(institute_name)

        # 2. generate key for uploading file
        key = storage_service_key(
            bucket,
            folder_name=institute_name,
            file_name=edx_video_id,
        )

        # 3. set meta data for the file
        for accessor, key_name, metadata_name in [
            (course.video_upload_pipeline.get, 'Institute_Name', 'institute'),
            (course.video_upload_pipeline.get, 'Access_Token', 'institute_token'),
            (file.get, 'file_name', 'user_supplied_file_name'),
            (course.get_attr, 'org', 'course_org'),
            (course.get_attr, 'course', 'course_number'),
            (course.get_attr, 'run', 'course_run'),
        ]:
            key.set_metadata(metadata_name, accessor(key_name))

        # 4. generate URL
        KEY_EXPIRATION_IN_SECONDS = 3600
        file_upload_urls[file['file_name']] = key.generate_url(KEY_EXPIRATION_IN_SECONDS, 'PUT')

        # TODO 5. persist edx_video_id

    return file_upload_urls


def generate_edx_video_id(institute_name):
    """
    Generates and returns an edx-video-id to uniquely identify a new logical video.
    """
    return "{}-{}".format(institute_name, uuid4())


def storage_service_bucket():
    """
    Returns a bucket in a cloud-based storage service for video uploads.
    """
    conn = S3Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY
    )
    return conn.get_bucket(settings.VIDEO_UPLOAD_PIPELINE['BUCKET'])


def storage_service_key(bucket, folder_name, file_name):
    """
    Returns a key to the given file in the given folder in the given bucket for video uploads.
    """
    key_name = "{}/{}/{}".format(
        settings.VIDEO_UPLOAD_PIPELINE['ROOT_PATH'],
        folder_name,
        file_name
    )
    return Key(bucket, key_name)
