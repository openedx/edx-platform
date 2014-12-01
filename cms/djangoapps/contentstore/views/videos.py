"""
Views related to the video upload feature
"""

from boto import s3
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from opaque_keys.edx.keys import CourseKey
from edxval.api import create_video, get_videos_for_ids

from xmodule.modulestore.django import modulestore
from xmodule.assetstore import AssetMetadata
from util.json_request import expect_json, JsonResponse

from .course import get_course_and_check_access


__all__ = ['videos_handler']


# String constant used in asset keys to identify video assets.
VIDEO_ASSET_TYPE = 'video'

# Default expiration, in seconds, of one-time URLs used for uploading videos.
KEY_EXPIRATION_IN_SECONDS = 3600


@expect_json
@login_required
@require_http_methods(("GET", "POST"))
def videos_handler(request, course_key_string):
    """
    The restful handler for video uploads.

    GET
        json: return json representing the videos that have been uploaded and their statuses
    POST
        json: upload a set of videos
    """
    # The feature flag should be enabled
    assert settings.FEATURES['ENABLE_VIDEO_UPLOAD_PIPELINE']

    course_key = CourseKey.from_string(course_key_string)

    # For now, assume all studio users that have access to the course can upload videos.
    # In the future, we plan to add a new org-level role for video uploaders.
    course = get_course_and_check_access(course_key, request.user)

    # Check whether the video upload feature is configured for this course
    if not course.video_pipeline_configured:
        return JsonResponse({"error": _("Course not configured properly for video upload.")}, status=404)

    if request.method == 'GET':
        return videos_index_json(course)
    else:
        return videos_post(course, request)


def _get_videos(course):
    """
    Returns the list of videos from VAL corresponding to the videos listed in
    the asset metadata store
    """
    edx_videos_ids = [
        v.asset_id.path
        for v in modulestore().get_all_asset_metadata(course.id, VIDEO_ASSET_TYPE)
    ]
    return list(get_videos_for_ids(edx_videos_ids))


def videos_index_json(course):
    """
    Returns a JSON in the following format: {
        videos: [
            {
                edx_video_id: xxx,
                file_name: xxx,
                date_uploaded: xxx,
                status: xxx,

                encodings: [{
                    url: url of the video,
                    file_size: size of the video in bytes,
                    profile: {
                        profile_name: ID of the profile
                        extension: 3 letter extension of video
                        width: horizontal pixel resolution
                        height: vertical pixel resolution
                    }
                }]
            },
            ...
        ]
    }
    """
    return JsonResponse({'videos': _get_videos(course)}, status=200)


def videos_post(course, request):
    """
    Input (JSON): {
        files: [
            { file_name: xxx },
            ...
        ]
    }
    Returns (JSON): {
        files: [
            { file_name: xxx, upload_url: xxx },
            ...
        ]
    }
    """
    bucket = storage_service_bucket()
    course_video_upload_token = course.video_upload_pipeline['course_video_upload_token']

    video_files = request.json['files']
    for video_file in video_files:
        file_name = video_file['file_name']

        # 1. generate edx_video_id
        edx_video_id = generate_edx_video_id()

        # 2. generate key for uploading file
        key = storage_service_key(bucket, file_name=edx_video_id)

        # 3. set meta data for the file
        for metadata_name, value in [
            ('course_video_upload_token', course_video_upload_token),
            ('user_supplied_file_name', file_name),
            ('course_key', unicode(course.id)),
        ]:
            key.set_metadata(metadata_name, value)

        # 4. generate URL
        video_file['upload-url'] = key.generate_url(
            KEY_EXPIRATION_IN_SECONDS,
            'PUT',
            headers={"Content-Type": video_file["content_type"]}
        )

        # 5. persist edx_video_id as uploaded through this course
        video_meta_data = AssetMetadata(
            course.id.make_asset_key(VIDEO_ASSET_TYPE, edx_video_id),
            fields={'file_name': file_name}
        )
        modulestore().save_asset_metadata(video_meta_data, request.user.id)

        # 6. persist edx_video_id in VAL
        create_video({
            'edx_video_id': edx_video_id,
            'status': 'upload',
            'client_video_id': file_name,
            'duration': 0,
            'encoded_videos': [],
        })

    return JsonResponse({'files': video_files}, status=200)


def generate_edx_video_id():
    """
    Generates and returns an edx-video-id to uniquely identify a new logical video.
    """
    return "edx-vid-v1-{}".format(uuid4())


def storage_service_bucket():
    """
    Returns a bucket in a cloud-based storage service for video uploads.
    """
    conn = s3.connection.S3Connection(
        getattr(settings, "AWS_ACCESS_KEY_ID", ""),
        getattr(settings, "AWS_SECRET_ACCESS_KEY", "")
    )
    return conn.get_bucket(settings.VIDEO_UPLOAD_PIPELINE['BUCKET'])


def storage_service_key(bucket, file_name):
    """
    Returns a key to the given file in the given folder in the given bucket for video uploads.
    """
    key_name = "{}/{}".format(
        settings.VIDEO_UPLOAD_PIPELINE['ROOT_PATH'],
        file_name
    )
    return s3.key.Key(bucket, key_name)
