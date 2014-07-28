"""
Handlers for video module.

StudentViewHandlers are handlers for video module instance.
StudioViewHandlers are handlers for video descriptor instance.
"""
import os
import json
import logging
from webob import Response

from xblock.core import XBlock

from xmodule.exceptions import NotFoundError
from xmodule.fields import RelativeTime

from .transcripts_utils import (
    get_or_create_sjson,
    TranscriptException,
    TranscriptsGenerationException,
    generate_sjson_for_all_speeds,
    youtube_speed_dict,
    Transcript,
    save_to_store,
    subs_filename
)


log = logging.getLogger(__name__)


# Disable no-member warning:
# pylint: disable=E1101


class VideoStudentViewHandlers(object):
    """
    Handlers for video module instance.
    """

    def handle_ajax(self, dispatch, data):
        """
        Update values of xfields, that were changed by student.
        """
        accepted_keys = [
            'speed', 'saved_video_position', 'transcript_language',
            'transcript_download_format', 'youtube_is_available'
        ]

        conversions = {
            'speed': json.loads,
            'saved_video_position': RelativeTime.isotime_to_timedelta,
            'youtube_is_available': json.loads,
        }

        if dispatch == 'save_user_state':
            for key in data:
                if hasattr(self, key) and key in accepted_keys:
                    if key in conversions:
                        value = conversions[key](data[key])
                    else:
                        value = data[key]

                    setattr(self, key, value)

                    if key == 'speed':
                        self.global_speed = self.speed

            return json.dumps({'success': True})

        log.debug(u"GET {0}".format(data))
        log.debug(u"DISPATCH {0}".format(dispatch))

        raise NotFoundError('Unexpected dispatch type')

    def translation(self, youtube_id):
        """
        This is called to get transcript file for specific language.

        youtube_id: str: must be one of youtube_ids or None if HTML video

        Logic flow:

        If youtube_id doesn't exist, we have a video in HTML5 mode. Otherwise,
        video video in Youtube or Flash modes.

        if youtube:
            If english -> give back youtube_id subtitles:
                Return what we have in contentstore for given youtube_id.
            If non-english:
                a) extract youtube_id from srt file name.
                b) try to find sjson by youtube_id and return if successful.
                c) generate sjson from srt for all youtube speeds.
        if non-youtube:
            If english -> give back `sub` subtitles:
                Return what we have in contentstore for given subs_if that is stored in self.sub.
            If non-english:
                a) try to find previously generated sjson.
                b) otherwise generate sjson from srt and return it.

        Filenames naming:
            en: subs_videoid.srt.sjson
            non_en: uk_subs_videoid.srt.sjson

        Raises:
            NotFoundError if for 'en' subtitles no asset is uploaded.
        """
        if youtube_id:
            # Youtube case:
            if self.transcript_language == 'en':
                return Transcript.asset(self.location, youtube_id).data

            youtube_ids = youtube_speed_dict(self)
            assert youtube_id in youtube_ids

            try:
                sjson_transcript = Transcript.asset(self.location, youtube_id, self.transcript_language).data
            except (NotFoundError):
                log.info("Can't find content in storage for %s transcript: generating.", youtube_id)
                generate_sjson_for_all_speeds(
                    self,
                    self.transcripts[self.transcript_language],
                    {speed: youtube_id for youtube_id, speed in youtube_ids.iteritems()},
                    self.transcript_language
                )
                sjson_transcript = Transcript.asset(self.location, youtube_id, self.transcript_language).data

            return sjson_transcript
        else:
            # HTML5 case
            if self.transcript_language == 'en':
                return Transcript.asset(self.location, self.sub).data
            else:
                return get_or_create_sjson(self)

    def get_transcript(self, transcript_format='srt'):
        """
        Returns transcript, filename and MIME type.

        Raises:
            - NotFoundError if cannot find transcript file in storage.
            - ValueError if transcript file is empty or incorrect JSON.
            - KeyError if transcript file has incorrect format.

        If language is 'en', self.sub should be correct subtitles name.
        If language is 'en', but if self.sub is not defined, this means that we
        should search for video name in order to get proper transcript (old style courses).
        If language is not 'en', give back transcript in proper language and format.
        """
        lang = self.transcript_language

        if lang == 'en':
            if self.sub:  # HTML5 case and (Youtube case for new style videos)
                transcript_name = self.sub
            elif self.youtube_id_1_0:  # old courses
                transcript_name = self.youtube_id_1_0
            else:
                log.debug("No subtitles for 'en' language")
                raise ValueError

            data = Transcript.asset(self.location, transcript_name, lang).data
            filename = u'{}.{}'.format(transcript_name, transcript_format)
            content = Transcript.convert(data, 'sjson', transcript_format)
        else:
            data = Transcript.asset(self.location, None, None, self.transcripts[lang]).data
            filename = u'{}.{}'.format(os.path.splitext(self.transcripts[lang])[0], transcript_format)
            content = Transcript.convert(data, 'srt', transcript_format)

        if not content:
            log.debug('no subtitles produced in get_transcript')
            raise ValueError

        return content, filename, Transcript.mime_types[transcript_format]

    def get_static_transcript(self, request):
        """
        Courses that are imported with the --nostatic flag do not show
        transcripts/captions properly even if those captions are stored inside
        their static folder. This adds a last resort method of redirecting to
        the static asset path of the course if the transcript can't be found
        inside the contentstore and the course has the static_asset_path field
        set.
        """
        response = Response(status=404)
        # Only do redirect for English
        if not self.transcript_language == 'en':
            return response

        video_id = request.GET.get('videoId', None)
        if video_id:
            transcript_name = video_id
        else:
            transcript_name = self.sub

        if transcript_name:
            # Get the asset path for course
            asset_path = None
            course = self.descriptor.runtime.modulestore.get_course(self.course_id)
            if course.static_asset_path:
                asset_path = course.static_asset_path
            else:
                # It seems static_asset_path is not set in any XMLModuleStore courses.
                asset_path = getattr(course, 'data_dir', '')

            if asset_path:
                response = Response(
                    status=307,
                    location='/static/{0}/{1}'.format(
                        asset_path,
                        subs_filename(transcript_name, self.transcript_language)
                    )
                )
        return response

    @XBlock.handler
    def transcript(self, request, dispatch):
        """
        Entry point for transcript handlers for student_view.

        Request GET may contain `videoId` for `translation` dispatch.

        Dispatches, (HTTP GET):
            /translation/[language_id]
            /download
            /available_translations/

        Explanations:
            `download`: returns SRT or TXT file.
            `translation`: depends on HTTP methods:
                    Provide translation for requested language, SJSON format is sent back on success,
                    Proper language_id should be in url.
            `available_translations`:
                    Returns list of languages, for which transcript files exist.
                    For 'en' check if SJSON exists. For non-`en` check if SRT file exists.
        """
        if dispatch.startswith('translation'):

            language = dispatch.replace('translation', '').strip('/')

            if not language:
                log.info("Invalid /translation request: no language.")
                return Response(status=400)

            if language not in ['en'] + self.transcripts.keys():
                log.info("Video: transcript facilities are not available for given language.")
                return Response(status=404)

            if language != self.transcript_language:
                self.transcript_language = language

            try:
                transcript = self.translation(request.GET.get('videoId', None))
            except (TypeError, NotFoundError) as ex:
                log.info(ex.message)
                # Try to return static URL redirection as last resort
                # if no translation is required
                return self.get_static_transcript(request)
            except (
                TranscriptException,
                UnicodeDecodeError,
                TranscriptsGenerationException
            ) as ex:
                log.info(ex.message)
                response = Response(status=404)
            else:
                response = Response(transcript, headerlist=[('Content-Language', language)])
                response.content_type = Transcript.mime_types['sjson']

        elif dispatch == 'download':
            try:
                transcript_content, transcript_filename, transcript_mime_type = self.get_transcript(self.transcript_download_format)
            except (NotFoundError, ValueError, KeyError, UnicodeDecodeError):
                log.debug("Video@download exception")
                return Response(status=404)
            else:
                response = Response(
                    transcript_content,
                    headerlist=[
                        ('Content-Disposition', 'attachment; filename="{}"'.format(transcript_filename.encode('utf8'))),
                        ('Content-Language', self.transcript_language),
                    ]
                )
                response.content_type = transcript_mime_type

        elif dispatch == 'available_translations':
            available_translations = []
            if self.sub:  # check if sjson exists for 'en'.
                try:
                    Transcript.asset(self.location, self.sub, 'en')
                except NotFoundError:
                    pass
                else:
                    available_translations = ['en']
            for lang in self.transcripts:
                try:
                    Transcript.asset(self.location, None, None, self.transcripts[lang])
                except NotFoundError:
                    continue
                available_translations.append(lang)
            if available_translations:
                response = Response(json.dumps(available_translations))
                response.content_type = 'application/json'
            else:
                response = Response(status=404)
        else:  # unknown dispatch
            log.debug("Dispatch is not allowed")
            response = Response(status=404)

        return response


class VideoStudioViewHandlers(object):
    """
    Handlers for Studio view.
    """
    @XBlock.handler
    def studio_transcript(self, request, dispatch):
        """
        Entry point for Studio transcript handlers.

        Dispatches:
            /translation/[language_id] - language_id sould be in url.

        `translation` dispatch support following HTTP methods:
            `POST`:
                Upload srt file. Check possibility of generation of proper sjson files.
                For now, it works only for self.transcripts, not for `en`.
                Do not update self.transcripts, as fields are updated on save in Studio.
            `GET:
                Return filename from storage. SRT format is sent back on success. Filename should be in GET dict.

        We raise all exceptions right in Studio:
            NotFoundError:
                Video or asset was deleted from module/contentstore, but request came later.
                Seems impossible to be raised. module_render.py catches NotFoundErrors from here.

            /translation POST:
                TypeError:
                    Unjsonable filename or content.
                TranscriptsGenerationException, TranscriptException:
                    no SRT extension or not parse-able by PySRT
                UnicodeDecodeError: non-UTF8 uploaded file content encoding.
        """
        _ = self.runtime.service(self, "i18n").ugettext

        if dispatch.startswith('translation'):
            language = dispatch.replace('translation', '').strip('/')

            if not language:
                log.info("Invalid /translation request: no language.")
                return Response(status=400)

            if request.method == 'POST':
                subtitles = request.POST['file']
                save_to_store(subtitles.file.read(), unicode(subtitles.filename), 'application/x-subrip', self.location)
                generate_sjson_for_all_speeds(self, unicode(subtitles.filename), {}, language)
                response = {'filename': unicode(subtitles.filename), 'status': 'Success'}
                return Response(json.dumps(response), status=201)

            elif request.method == 'GET':

                filename = request.GET.get('filename')
                if not filename:
                    log.info("Invalid /translation request: no filename in request.GET")
                    return Response(status=400)

                content = Transcript.get_asset(self.location, filename).data
                response = Response(content, headerlist=[
                    ('Content-Disposition', 'attachment; filename="{}"'.format(filename.encode('utf8'))),
                    ('Content-Language', language),
                ])
                response.content_type = Transcript.mime_types['srt']

        else:  # unknown dispatch
            log.debug("Dispatch is not allowed")
            response = Response(status=404)

        return response
