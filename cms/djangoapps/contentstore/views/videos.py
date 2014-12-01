"""
Views related to the video upload feature
"""
from boto import s3
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_http_methods

from edxval.api import create_video, get_videos_for_ids
from opaque_keys.edx.keys import CourseKey

from util.json_request import expect_json, JsonResponse
from xmodule.assetstore import AssetMetadata
from xmodule.modulestore.django import modulestore

from .course import get_course_and_check_access


__all__ = ["videos_handler"]


# String constant used in asset keys to identify video assets.
VIDEO_ASSET_TYPE = "video"

# Default expiration, in seconds, of one-time URLs used for uploading videos.
KEY_EXPIRATION_IN_SECONDS = 86400


@expect_json
@login_required
@require_http_methods(("GET", "POST"))
def videos_handler(request, course_key_string):
    """
    The restful handler for video uploads.

    GET
        json: return json representing the videos that have been uploaded and
            their statuses
    POST
        json: create a new video upload; the actual files should not be provided
            to this endpoint but rather PUT to the respective upload_url values
            contained in the response
    """
    course_key = CourseKey.from_string(course_key_string)

    # For now, assume all studio users that have access to the course can upload videos.
    # In the future, we plan to add a new org-level role for video uploaders.
    course = get_course_and_check_access(course_key, request.user)

    if (
            not settings.FEATURES["ENABLE_VIDEO_UPLOAD_PIPELINE"] or
            not getattr(settings, "VIDEO_UPLOAD_PIPELINE", None) or
            not course or
            not course.video_pipeline_configured
    ):
        return HttpResponseNotFound()

    if request.method == 'GET':
        return videos_index_json(course)
    else:
        return videos_post(course, request)


def _get_videos(course):
    """
    Retrieves the list of videos from VAL corresponding to the videos listed in
    the asset metadata store and returns the needed subset of fields
    """
    edx_videos_ids = [
        v.asset_id.path
        for v in modulestore().get_all_asset_metadata(course.id, VIDEO_ASSET_TYPE)
    ]
    return list(
        {
            attr: video[attr]
            for attr in ["edx_video_id", "client_video_id", "created", "duration", "status"]
        }
        for video in get_videos_for_ids(edx_videos_ids)
    )


def videos_index_json(course):
    """
    Returns JSON in the following format:
    {
        "videos": [{
            "edx_video_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
            "client_video_id": "video.mp4",
            "created": "1970-01-01T00:00:00Z",
            "duration": 42.5,
            "status": "upload"
        }]
    }
    """
    return JsonResponse({"videos": _get_videos(course)}, status=200)


def videos_post(course, request):
    """
    Input (JSON):
    {
        "files": [{
            "file_name": "video.mp4",
            "content_type": "video/mp4"
        }]
    }

    Returns (JSON):
    {
        "files": [{
            "file_name": "video.mp4",
            "upload_url": "http://example.com/put_video"
        }]
    }

    The returned array corresponds exactly to the input array.
    """
    error = None
    if "files" not in request.json:
        error = "Request object is not JSON or does not contain 'files'"
    elif any(
            "file_name" not in file or "content_type" not in file
            for file in request.json["files"]
    ):
        error = "Request 'files' entry does not contain 'file_name' and 'content_type'"

    if error:
        return JsonResponse({"error": error}, status=400)

    bucket = storage_service_bucket()
    course_video_upload_token = course.video_upload_pipeline["course_video_upload_token"]
    req_files = request.json["files"]
    resp_files = []

    for req_file in req_files:
        file_name = req_file["file_name"]

        edx_video_id = unicode(uuid4())
        key = storage_service_key(bucket, file_name=edx_video_id)
        for metadata_name, value in [
            ("course_video_upload_token", course_video_upload_token),
            ("client_video_id", file_name),
            ("course_key", unicode(course.id)),
        ]:
            key.set_metadata(metadata_name, value)
        upload_url = key.generate_url(
            KEY_EXPIRATION_IN_SECONDS,
            "PUT",
            headers={"Content-Type": req_file["content_type"]}
        )

        # persist edx_video_id as uploaded through this course
        video_meta_data = AssetMetadata(course.id.make_asset_key(VIDEO_ASSET_TYPE, edx_video_id))
        modulestore().save_asset_metadata(video_meta_data, request.user.id)

        # persist edx_video_id in VAL
        create_video({
            "edx_video_id": edx_video_id,
            "status": "upload",
            "client_video_id": file_name,
            "duration": 0,
            "encoded_videos": [],
        })

        resp_files.append({"file_name": file_name, "upload_url": upload_url})

    return JsonResponse({"files": resp_files}, status=200)


def storage_service_bucket():
    """
    Returns an S3 bucket for video uploads.
    """
    conn = s3.connection.S3Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY
    )
    return conn.get_bucket(settings.VIDEO_UPLOAD_PIPELINE["BUCKET"])


def storage_service_key(bucket, file_name):
    """
    Returns an S3 key to the given file in the given bucket.
    """
    key_name = "{}/{}".format(
        settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH", ""),
        file_name
    )
    return s3.key.Key(bucket, key_name)
