"""
Views related to the transcript preferences feature
"""
import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST, require_GET
from edxval.api import (
    get_3rd_party_transcription_plans,
    get_video_transcript_data,
    update_transcript_credentials_state_for_org,
)
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.video_config.models import VideoTranscriptEnabledFlag
from openedx.core.djangoapps.video_pipeline.api import update_3rd_party_transcription_service_credentials
from util.json_request import JsonResponse, expect_json

from contentstore.views.videos import TranscriptProvider
from xmodule.video_module.transcripts_utils import Transcript

__all__ = ['transcript_credentials_handler', 'transcript_download_handler']


class TranscriptionProviderErrorType:
    """
    Transcription provider's error types enumeration.
    """
    INVALID_CREDENTIALS = 1


def validate_transcript_credentials(provider, **credentials):
    """
    Validates transcript credentials.

    Validations:
        Providers must be either 3PlayMedia or Cielo24.
        In case of:
            3PlayMedia - 'api_key' and 'api_secret_key' are required.
            Cielo24 - 'api_key' and 'username' are required.

        It ignores any extra/unrelated parameters passed in credentials and
        only returns the validated ones.
    """
    error_message, validated_credentials = '', {}
    valid_providers = get_3rd_party_transcription_plans().keys()
    if provider in valid_providers:
        must_have_props = []
        if provider == TranscriptProvider.THREE_PLAY_MEDIA:
            must_have_props = ['api_key', 'api_secret_key']
        elif provider == TranscriptProvider.CIELO24:
            must_have_props = ['api_key', 'username']

        missing = [must_have_prop for must_have_prop in must_have_props if must_have_prop not in credentials.keys()]
        if missing:
            error_message = u'{missing} must be specified.'.format(missing=' and '.join(missing))
            return error_message, validated_credentials

        validated_credentials.update({
            prop: credentials[prop] for prop in must_have_props
        })
    else:
        error_message = u'Invalid Provider {provider}.'.format(provider=provider)

    return error_message, validated_credentials


@expect_json
@login_required
@require_POST
def transcript_credentials_handler(request, course_key_string):
    """
    JSON view handler to update the transcript organization credentials.

    Arguments:
        request: WSGI request object
        course_key_string: A course identifier to extract the org.

    Returns:
        - A 200 response if credentials are valid and successfully updated in edx-video-pipeline.
        - A 404 response if transcript feature is not enabled for this course.
        - A 400 if credentials do not pass validations, hence not updated in edx-video-pipeline.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not VideoTranscriptEnabledFlag.feature_enabled(course_key):
        return HttpResponseNotFound()

    provider = request.json.pop('provider')
    error_message, validated_credentials = validate_transcript_credentials(provider=provider, **request.json)
    if error_message:
        response = JsonResponse({'error': error_message}, status=400)
    else:
        # Send the validated credentials to edx-video-pipeline.
        credentials_payload = dict(validated_credentials, org=course_key.org, provider=provider)
        error_response, is_updated = update_3rd_party_transcription_service_credentials(**credentials_payload)
        # Send appropriate response based on whether credentials were updated or not.
        if is_updated:
            # Cache credentials state in edx-val.
            update_transcript_credentials_state_for_org(org=course_key.org, provider=provider, exists=is_updated)
            response = JsonResponse(status=200)
        else:
            # Error response would contain error types and the following
            # error type is received from edx-video-pipeline whenever we've
            # got invalid credentials for a provider. Its kept this way because
            # edx-video-pipeline doesn't support i18n translations yet.
            error_type = error_response.get('error_type')
            if error_type == TranscriptionProviderErrorType.INVALID_CREDENTIALS:
                error_message = _('The information you entered is incorrect.')

            response = JsonResponse({'error': error_message}, status=400)

    return response


@login_required
@require_GET
def transcript_download_handler(request, course_key_string):
    """
    JSON view handler to download a transcript.

    Arguments:
        request: WSGI request object
        course_key_string: course key

    Returns:
        - A 200 response with SRT transcript file attached.
        - A 400 if there is a validation error.
        - A 404 if there is no such transcript or feature flag is disabled.
    """
    course_key = CourseKey.from_string(course_key_string)
    if not VideoTranscriptEnabledFlag.feature_enabled(course_key):
        return HttpResponseNotFound()

    missing = [attr for attr in ['edx_video_id', 'language_code'] if attr not in request.GET]
    if missing:
        return JsonResponse(
            {'error': _(u'Following parameters are required: {missing}.').format(missing=', '.join(missing))},
            status=400
        )

    edx_video_id = request.GET['edx_video_id']
    language_code = request.GET['language_code']
    transcript = get_video_transcript_data(video_ids=[edx_video_id], language_code=language_code)
    if transcript:
        name_and_extension = os.path.splitext(transcript['file_name'])
        basename, file_format = name_and_extension[0], name_and_extension[1][1:]
        transcript_filename = '{base_name}.srt'.format(base_name=basename.encode('utf8'))
        transcript_content = Transcript.convert(transcript['content'], input_format=file_format, output_format='srt')
        # Construct an HTTP response
        response = HttpResponse(transcript_content, content_type=Transcript.mime_types['srt'])
        response['Content-Disposition'] = 'attachment; filename="{filename}"'.format(filename=transcript_filename)
    else:
        response = HttpResponseNotFound()

    return response
