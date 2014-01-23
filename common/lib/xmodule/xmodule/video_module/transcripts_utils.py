"""
Utility functions for transcripts.
++++++++++++++++++++++++++++++++++
"""
import os
import copy
import json
import requests
import logging
from pysrt import SubRipTime, SubRipItem, SubRipFile
from lxml import etree

from xmodule.exceptions import NotFoundError
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore


log = logging.getLogger(__name__)


class TranscriptException(Exception):  # pylint disable=C0111
    pass


class TranscriptsGenerationException(Exception):  # pylint disable=C0111
    pass


class GetTranscriptsFromYouTubeException(Exception):  # pylint disable=C0111
    pass


class TranscriptsRequestValidationException(Exception):  # pylint disable=C0111
    pass


def generate_subs(speed, source_speed, source_subs):
    """
    Generate transcripts from one speed to another speed.

    Args:
    `speed`: float, for this speed subtitles will be generated,
    `source_speed`: float, speed of source_subs
    `source_subs`: dict, existing subtitles for speed `source_speed`.

    Returns:
    `subs`: dict, actual subtitles.
    """
    if speed == source_speed:
        return source_subs

    coefficient = 1.0 * speed / source_speed
    subs = {
        'start': [
            int(round(timestamp * coefficient)) for
            timestamp in source_subs['start']
        ],
        'end': [
            int(round(timestamp * coefficient)) for
            timestamp in source_subs['end']
        ],
        'text': source_subs['text']}
    return subs


def save_subs_to_store(subs, subs_id, item, language='en'):
    """
    Save transcripts into `StaticContent`.

    Args:
    `subs_id`: str, subtitles id
    `item`: video module instance
    `language`: two chars str ('uk'), language of translation of transcripts

    Returns: location of saved subtitles.
    """
    filedata = json.dumps(subs, indent=2)
    mime_type = 'application/json'
    filename = subs_filename(subs_id, language)
    content_location = asset_location(item.location, filename)
    content = StaticContent(content_location, filename, mime_type, filedata)
    contentstore().save(content)
    return content_location


def get_transcripts_from_youtube(youtube_id, settings, i18n):
    """
    Gets transcripts from youtube for youtube_id.

    Parses only utf-8 encoded transcripts.
    Other encodings are not supported at the moment.

    Returns (status, transcripts): bool, dict.
    """
    _ = i18n.ugettext

    utf8_parser = etree.XMLParser(encoding='utf-8')

    youtube_api = copy.deepcopy(settings.YOUTUBE_API)
    youtube_api['params']['v'] = youtube_id
    data = requests.get(youtube_api['url'], params=youtube_api['params'])

    if data.status_code != 200 or not data.text:
        msg = _("Can't receive transcripts from Youtube for {youtube_id}. Status code: {statuc_code}.").format(
            youtube_id=youtube_id,
            statuc_code=data.status_code
        )
        raise GetTranscriptsFromYouTubeException(msg)

    sub_starts, sub_ends, sub_texts = [], [], []
    xmltree = etree.fromstring(data.content, parser=utf8_parser)
    for element in xmltree:
        if element.tag == "text":
            start = float(element.get("start"))
            duration = float(element.get("dur", 0))  # dur is not mandatory
            text = element.text
            end = start + duration

            if text:
                # Start and end should be ints representing the millisecond timestamp.
                sub_starts.append(int(start * 1000))
                sub_ends.append(int((end + 0.0001) * 1000))
                sub_texts.append(text.replace('\n', ' '))

    return {'start': sub_starts, 'end': sub_ends, 'text': sub_texts}


def download_youtube_subs(youtube_subs, item, settings):
    """
    Download transcripts from Youtube and save them to assets.

    Args:
    youtube_subs: dictionary of `speed: youtube_id` key:value pairs.
    item: video module instance.

    Returns: None, if transcripts were successfully downloaded and saved.
    Otherwise raises GetTranscriptsFromYouTubeException.
    """
    i18n = item.runtime.service(item, "i18n")
    _ = i18n.ugettext

    highest_speed = highest_speed_subs = None
    missed_speeds = []
    # Iterate from lowest to highest speed and try to do download transcripts
    # from the Youtube service.
    for speed, youtube_id in sorted(youtube_subs.iteritems()):
        if not youtube_id:
            continue
        try:
            subs = get_transcripts_from_youtube(youtube_id, settings, i18n)
            if not subs:  # if empty subs are returned
                raise GetTranscriptsFromYouTubeException
        except GetTranscriptsFromYouTubeException:
            missed_speeds.append(speed)
            continue

        save_subs_to_store(subs, youtube_id, item)

        log.info(
            "Transcripts for YouTube id %s (speed %s)"
            "are downloaded and saved.", youtube_id, speed
        )

        highest_speed = speed
        highest_speed_subs = subs

    if not highest_speed:
        raise GetTranscriptsFromYouTubeException(_("Can't find any transcripts on the Youtube service."))

    # When we exit from the previous loop, `highest_speed` and `highest_speed_subs`
    # are the transcripts data for the highest speed available on the
    # Youtube service. We use the highest speed as main speed for the
    # generation other transcripts, cause during calculation timestamps
    # for lower speeds we just use multiplication instead of division.
    for speed in missed_speeds:  # Generate transcripts for missed speeds.
        save_subs_to_store(
            generate_subs(speed, highest_speed, highest_speed_subs),
            youtube_subs[speed],
            item
        )

        log.info(
            "Transcripts for YouTube id %s (speed %s)"
            "are generated from YouTube id %s (speed %s) and saved",
            youtube_subs[speed], speed,
            youtube_subs[highest_speed],
            highest_speed
        )


def remove_subs_from_store(subs_id, item, lang='en'):
    """
    Remove from store, if transcripts content exists.
    """
    try:
        content = asset(item.location, subs_id, lang)
        contentstore().delete(content.get_id())
        log.info("Removed subs %s from store", subs_id)
    except NotFoundError:
        pass


def generate_subs_from_source(speed_subs, subs_type, subs_filedata, item, language='en'):
    """Generate transcripts from source files (like SubRip format, etc.)
    and save them to assets for `item` module.
    We expect, that speed of source subs equal to 1

    :param speed_subs: dictionary {speed: sub_id, ...}
    :param subs_type: type of source subs: "srt", ...
    :param subs_filedata:unicode, content of source subs.
    :param item: module object.
    :param language: str, language of translation of transcripts
    :returns: True, if all subs are generated and saved successfully.
    """
    _ = item.runtime.service(item, "i18n").ugettext
    if subs_type != 'srt':
        raise TranscriptsGenerationException(_("We support only SubRip (*.srt) transcripts format."))
    try:
        srt_subs_obj = SubRipFile.from_string(subs_filedata)
    except Exception as ex:
        msg = _("Something wrong with SubRip transcripts file during parsing. Inner message is {error_message}").format(
            error_message=ex.message
        )
        raise TranscriptsGenerationException(msg)
    if not srt_subs_obj:
        raise TranscriptsGenerationException(_("Something wrong with SubRip transcripts file during parsing."))

    sub_starts = []
    sub_ends = []
    sub_texts = []

    for sub in srt_subs_obj:
        sub_starts.append(sub.start.ordinal)
        sub_ends.append(sub.end.ordinal)
        sub_texts.append(sub.text.replace('\n', ' '))

    subs = {
        'start': sub_starts,
        'end': sub_ends,
        'text': sub_texts}

    for speed, subs_id in speed_subs.iteritems():
        save_subs_to_store(
            generate_subs(speed, 1, subs),
            subs_id,
            item,
            language
        )

    return subs


def generate_srt_from_sjson(sjson_subs, speed):
    """Generate transcripts with speed = 1.0 from sjson to SubRip (*.srt).

    :param sjson_subs: "sjson" subs.
    :param speed: speed of `sjson_subs`.
    :returns: "srt" subs.
    """

    output = ''

    equal_len = len(sjson_subs['start']) == len(sjson_subs['end']) == len(sjson_subs['text'])
    if not equal_len:
        return output

    sjson_speed_1 = generate_subs(speed, 1, sjson_subs)

    for i in range(len(sjson_speed_1['start'])):
        item = SubRipItem(
            index=i,
            start=SubRipTime(milliseconds=sjson_speed_1['start'][i]),
            end=SubRipTime(milliseconds=sjson_speed_1['end'][i]),
            text=sjson_speed_1['text'][i]
        )
        output += (unicode(item))
        output += '\n'
    return output


def copy_or_rename_transcript(new_name, old_name, item, delete_old=False, user=None):
    """
    Renames `old_name` transcript file in storage to `new_name`.

    If `old_name` is not found in storage, raises `NotFoundError`.
    If `delete_old` is True, removes `old_name` files from storage.
    """
    filename = 'subs_{0}.srt.sjson'.format(old_name)
    content_location = StaticContent.compute_location(
        item.location.org, item.location.course, filename
    )
    transcripts = contentstore().find(content_location).data
    save_subs_to_store(json.loads(transcripts), new_name, item)
    item.sub = new_name
    item.save_with_metadata(user)
    if delete_old:
        remove_subs_from_store(old_name, item)


def get_html5_ids(html5_sources):
    """
    Helper method to parse out an HTML5 source into the ideas
    NOTE: This assumes that '/' are not in the filename
    """
    html5_ids = [x.split('/')[-1].rsplit('.', 1)[0] for x in html5_sources]
    return html5_ids


def manage_video_subtitles_save(item, user, old_metadata=None, generate_translation=False):
    """
    Does some specific things, that can be done only on save.

    Video player item has some video fields: HTML5 ones and Youtube one.

    If value of `sub` field of `new_item` is cleared, transcripts should be removed.

    `item` is video module instance with updated values of fields,
    but actually have not been saved to store yet.

    `old_metadata` contains old values of XFields.

    # 1.
    If value of `sub` field of `new_item` is different from values of video fields of `new_item`,
    and `new_item.sub` file is present, then code in this function creates copies of
    `new_item.sub` file with new names. That names are equal to values of video fields of `new_item`
    After that `sub` field of `new_item` is changed to one of values of video fields.
    This whole action ensures that after user changes video fields, proper `sub` files, corresponding
    to new values of video fields, will be presented in system.

    # 2. Generate transcripts translation only  when user clicks `save` button, not while switching tabs.
    a) delete sjson translation for those languages, which were removed from `item.transcripts`.
        Note: we are not deleting old SRT files to give user more flexibility.
    b) For all SRT files in`item.transcripts` regenerate new SJSON files.
        (To avoid confusing situation if you attempt to correct a translation by uploading
        a new version of the SRT file with same name).
    """

    # 1.
    html5_ids = get_html5_ids(item.html5_sources)
    possible_video_id_list = [item.youtube_id_1_0] + html5_ids
    sub_name = item.sub
    for video_id in possible_video_id_list:
        if not video_id:
            continue
        if not sub_name:
            remove_subs_from_store(video_id, item)
            continue
        # copy_or_rename_transcript changes item.sub of module
        try:
            # updates item.sub with `video_id`, if it is successful.
            copy_or_rename_transcript(video_id, sub_name, item, user=user)
        except NotFoundError:
            # subtitles file `sub_name` is not presented in the system. Nothing to copy or rename.
            log.debug(
                "Copying %s file content to %s name is failed, "
                "original file does not exist.",
                sub_name, video_id
            )

    # 2.
    if generate_translation:
        old_langs = set(old_metadata.get('transcripts', {})) if old_metadata else set()
        new_langs = set(item.transcripts)

        for lang in old_langs.difference(new_langs):  # 2a
            for video_id in possible_video_id_list:
                if video_id:
                    remove_subs_from_store(video_id, item, lang)

        reraised_message = ''
        for lang in new_langs:  # 2b
            try:
                generate_sjson_for_all_speeds(
                    item,
                    item.transcripts[lang],
                    {speed: subs_id for subs_id, speed in youtube_speed_dict(item).iteritems()},
                    lang,
                )
            except TranscriptException as ex:
                item.transcripts.pop(lang)  # remove key from transcripts because proper srt file does not exist in assets.
                reraised_message += ' ' + ex.message
        if reraised_message:
            item.save_with_metadata(user)
            raise TranscriptException(reraised_message)


def youtube_speed_dict(item):
    """
    Returns {speed: youtube_ids, ...} dict for existing youtube_ids
    """
    yt_ids = [item.youtube_id_0_75, item.youtube_id_1_0, item.youtube_id_1_25, item.youtube_id_1_5]
    yt_speeds = [0.75, 1.00, 1.25, 1.50]
    youtube_ids = {p[0]: p[1] for p in zip(yt_ids, yt_speeds) if p[0]}
    return youtube_ids


def subs_filename(subs_id, lang='en'):
    """
    Generate proper filename for storage.
    """
    if lang == 'en':
        return 'subs_{0}.srt.sjson'.format(subs_id)
    else:
        return '{0}_subs_{1}.srt.sjson'.format(lang, subs_id)


def asset_location(location, filename):
    """
    Return asset location.

    `location` is module location.
    """
    return StaticContent.compute_location(
        location.org, location.course, filename
    )


def asset(location, subs_id, lang='en', filename=None):
    """
    Get asset from contentstore, asset location is built from subs_id and lang.

    `location` is module location.
    """
    return contentstore().find(
        asset_location(
            location,
            subs_filename(subs_id, lang) if not filename else filename
        )
    )


def generate_sjson_for_all_speeds(item, user_filename, result_subs_dict, lang):
    """
    Generates sjson from srt for given lang.

    `item` is module object.
    """
    try:
        srt_transcripts = contentstore().find(asset_location(item.location, user_filename))
    except NotFoundError as ex:
        raise TranscriptException("{}: Can't find uploaded transcripts: {}".format(ex.message, user_filename))

    if not lang:
        lang = item.transcript_language

    generate_subs_from_source(
        result_subs_dict,
        os.path.splitext(user_filename)[1][1:],
        srt_transcripts.data.decode('utf8'),
        item,
        lang
    )


def get_or_create_sjson(item):
    """
    Get sjson if already exists, otherwise generate it.

    Generate sjson with subs_id name, from user uploaded srt.
    Subs_id is extracted from srt filename, which was set by user.

    Raises:
        TranscriptException: when srt subtitles do not exist,
        and exceptions from generate_subs_from_source.

    `item` is module object.
    """
    user_filename = item.transcripts[item.transcript_language]
    user_subs_id = os.path.splitext(user_filename)[0]
    source_subs_id, result_subs_dict = user_subs_id, {1.0: user_subs_id}
    try:
        sjson_transcript = asset(item.location, source_subs_id, item.transcript_language).data
    except (NotFoundError):  # generating sjson from srt
        generate_sjson_for_all_speeds(item, user_filename, result_subs_dict, item.transcript_language)
    sjson_transcript = asset(item.location, source_subs_id, item.transcript_language).data
    return sjson_transcript
