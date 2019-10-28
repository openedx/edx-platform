TWITTER_TWEET_TEXT_FMT = 'I just completed @PhilanthropyUni\'s free online {course_name} ' \
                         'course and earned this certificate. Start learning today: ' \
                         '{base_url}/{course_url}/{course_id}/{about_url}'
TWITTER_META_TITLE_FMT = "I just completed Philanthropy University\'s {course_name} course!"
SOCIAL_MEDIA_SHARE_URL_FMT = "{base_url}/achievements/{certificate_uuid}"
COURSE_URL_FMT = "{base_url}/{course_url}/{course_id}/{about_url}"
PAGE_HEIGHT='page-height'
PAGE_WIDTH='page-width'
PDF_RESPONSE_HEADER = 'attachment; filename="{certificate_pdf_name}.pdf"' # download pdf for end user
PDFKIT_HTML_STRING='<html><head><style>body,html{{padding:0;margin:0;font-size:0;}}</style></head><body>{image_tag}</body></html>'
PDFKIT_IMAGE_PATH = False # Use false instead of output path to save pdf to a python variable
PDFKIT_IMAGE_TAG='<img src="data:image/png;base64,{base64_img}"/>'
PDFKIT_OPTIONS = {
    PAGE_HEIGHT: '{}px',
    PAGE_WIDTH: '{}px',
    'disable-smart-shrinking': None,  # By default pdfkit scale/shrink html, in our case we do not need that
    'encoding': "UTF-8",
    'margin-bottom': '0.0in',
    'margin-left': '0.0in',
    'margin-right': '0.0in',
    'margin-top': '0.0in',
    'no-outline': None,
    'print-media-type': None
}
TMPDIR="/tmp" # path of directory to store files (certificate images) temporarily
