''' Tests mechanism for obtaining language-specific transcript links from youtube video pages
Note that tests that work with these links are located elsewhere (test_video.py)
'''
from ..video_module.transcripts_utils import get_transcript_link_from_youtube

from unittest import mock, TestCase


YOUTUBE_VIDEO_ID = "z-LoKnweV6w"

# Use CAPTION_URL_TEMPLATE.format(<youtube_video_ID>, <ampersand_encoding>, <language_code>)
# to get either the HTML rendition or the json rendition of the link used to obtain a youtube video's subtitles
#
# Parameterized with
# {0} - The youtube video ID whose captions you want
# {1} - Either \u0026 for use with UTF-8 encoded HTML, or '&' for use with json
# {2} - Language code (e.g., "en")
CAPTION_URL_TEMPLATE = "https: //www.youtube.com/api/timedtext?v = {0}{1}caps = asr{1}xoaf = 5{1}hl = {2}{1}\
ip = 0.0.0.0{1}ipbits = 0{1}expire = 1667281544{1}sparams = ip, ipbits, expire, v, caps, xoaf{1}\
signature = 3A2A34F0A1FB11B3825FF54D4238B6CC415877E8.058892{1}key = yt8{1}kind = asr{1}lang = {2}"

UTF8_AMPERSAND = '\\u0026'

# These caption link templates have tailored uses and parameterize on the language code only
#
# Parameterized with
# {0} - Language code (e.g., "en")
CAPTION_URL_UTF8_ENCODED_TEMPLATE = CAPTION_URL_TEMPLATE.format(YOUTUBE_VIDEO_ID, UTF8_AMPERSAND, "{0}")
CAPTION_URL_UTF8_DECODED_TEMPLATE = CAPTION_URL_TEMPLATE.format(YOUTUBE_VIDEO_ID, "&", "{0}")

# Macro providing the HTML returned by our mock GET operation on the youtube video page
# This is not valid HTML, but that's OK, as we'll only be using it to confirm the regex
# search on the 'playerCaptionsTrackListRenderer' subtree.
#
# Packed quality (i.e., no spaces) is essential for these tests to work! Introduction
# of spaces before or after the colon signs causes the regex matching to stop working.
#
# Parameterized with
# {0} - the URL that obtains the selected video's caption
# {1} - Language code (e.g., "en")
YOUTUBE_HTML_TEMPLATE = "HTML content that comes before the captions..." \
                        "\"captions\":{{\"playerCaptionsTracklistRenderer\":" \
                        "{{\"captionTracks\":[{{\"baseUrl\":\"{0}\"," \
                        "\"name\":{{\"simpleText\":\"(Caption language name in local language)\"}}," \
                        "\"vssId\":\".{1}\",\"languageCode\":\"{1}\"," \
                        "\"isTranslatable\":true}}]}}}}HTML content that comes after the captions..."


class YoutubeVideoHTMLResponse:
    '''Generates substitute HTTP GET responses used when mocking the GET operation to a youtube video page'''

    @classmethod
    def with_caption_link(cls, language_code):
        '''Generates a GET response of HTML with a single caption of the specified language code
            language_code = "en" for english
        '''
        caption_link = CAPTION_URL_UTF8_ENCODED_TEMPLATE.format(language_code)
        html_with_embedded_link = YOUTUBE_HTML_TEMPLATE.format(caption_link, language_code)
        return cls.MockResponse(html_with_embedded_link)

    @classmethod
    def with_no_caption_links(cls):
        '''Generates a GET response of (invalid) HTML lacking any captions within it.
        This fake HTML is nevered rendered; it's only intended as a source for a regex
        search
        '''
        return cls.MockResponse("No caption URL info for regex to find here")

    class MockResponse:
        '''An object fit to be returned from a an HTTP GET operation, exposing
        a UTF-8 encoded version of the youtube_html input string in its content attribute'''
        def __init__(self, youtube_html):
            self.get_content = bytearray(youtube_html, 'UTF-8')

        def content(self):
            return self.get_content


class TranscriptsUtilsTest(TestCase):
    ''' Tests utility fucntions for transcripts (in video_module)'''

    @mock.patch('requests.get')
    def test_get_transcript_link_from_youtube(self, mock_get):
        '''Happy path test: english caption link returned when video page HTML has one english caption'''
        language_code = 'en'
        mock_get.return_value = YoutubeVideoHTMLResponse.with_caption_link(language_code)

        language_specific_caption_link = get_transcript_link_from_youtube(YOUTUBE_VIDEO_ID)
        self.assertEqual(language_specific_caption_link, CAPTION_URL_UTF8_DECODED_TEMPLATE.format(language_code))

    @ mock.patch('requests.get')
    def test_get_caption_no_english_caption(self, mock_get):
        '''No caption link returned when video page HTML contains no caption in English'''
        language_code = 'fr'
        mock_get.return_value = YoutubeVideoHTMLResponse.with_caption_link(language_code)

        english_language_caption_link = get_transcript_link_from_youtube(YOUTUBE_VIDEO_ID)
        self.assertEqual(english_language_caption_link, None)

    @ mock.patch('requests.get')
    def test_get_caption_no_captions_in_HTML(self, mock_get):
        ''' No caption link returned when video page HTML contains no captions at all'''
        mock_get.return_value = YoutubeVideoHTMLResponse.with_no_caption_links()

        english_language_caption_link = get_transcript_link_from_youtube(YOUTUBE_VIDEO_ID)
        self.assertEqual(english_language_caption_link, None)
