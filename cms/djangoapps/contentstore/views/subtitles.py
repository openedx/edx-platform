"""Developer's workflow for the timed transcripts in CMS.

We provide 3 api methods to work with timed transcript
(mitx/cms/urls.py:23-25):
- "upload_subtitles"
- "download_subtitles"
- "check_subtitles"

"upload_subtitles" method is used for uploading SRT transcripts for the
HTML5 video module (we don't allow this functionality for the Youtube video).

URL is created like a "create_item", "save_item", "delete_item" etc.
Method: POST
Parameters:
    - id - location ID of the Xmodule
    - file - BLOB file
Response: JSON – {'success': true/false}


"download_subtitles" method is used for downloading SRT transcripts for the
HTML5 video module (we don't allow this functionality for the Youtube video).

URL is created like a "create_item", "save_item", "delete_item" etc.
Method: GET
Parameters:
    - id - location ID of the Xmodule
Response:
    HTTP 404
    or
    HTTP 200 + BLOB of SRT file


"check_subtitles" method is used for checking availability timed transcripts
for the HTML5 video module. So, if `item.sub` is not empty, and that file is
existed in the storage - the method answers positively.

URL is created like a "create_item", "save_item", "delete_item" etc.
Method: GET
Parameters:
    - id - location ID of the Xmodule
Response: JSON – {'success': true/false}
"""
