__author__ = 'aamir'

import re
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.contentstore.content import StaticContent


def parse_video_tag(video_with_html):
    """
    Gives the video ID from video's html
    Because the client really only wants the author to specify the youtube key, that's all we send to and get from the
    client. The problem is that the db stores the html markup as well (which, of course, makes any sitewide changes to
    how we do videos next to impossible.)
    """
    video_id = None
    if video_with_html:
        string_matcher = re.search(r'(?<=embed/)[a-zA-Z0-9_-]+', video_with_html)
        if string_matcher is None:
            string_matcher = re.search(r'<?=\d+:[a-zA-Z0-9_-]+', video_with_html)
        if string_matcher:
            video_id = string_matcher.group(0)
    return video_id
