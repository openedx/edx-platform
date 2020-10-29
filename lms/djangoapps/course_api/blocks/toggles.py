"""
Toggles for Course API.
"""


from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace


COURSE_BLOCKS_API_NAMESPACE = WaffleFlagNamespace(name=u'course_blocks_api')

# Waffle flag to hide access denial message.
# .. toggle_name: course_blocks_api.hide_access_denials
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: ??
# .. toggle_category: course api
# .. toggle_use_cases: incremental_release, open_edx
# .. toggle_creation_date: 2019-04-10
# .. toggle_expiration_date: ??
# .. toggle_warnings: ??
# .. toggle_tickets: ??
# .. toggle_status: ??
HIDE_ACCESS_DENIALS_FLAG = WaffleFlag(
    waffle_namespace=COURSE_BLOCKS_API_NAMESPACE,
    flag_name=u'hide_access_denials',
    flag_undefined_default=False
)

# Waffle course override to rewrite video URLs for videos that have encodings available.
# .. toggle_name: course_blocks_api.enable_video_url_rewrite
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Controlled rollout for video URL re-write utility to serve videos from edX CDN.
# .. toggle_category: course api
# .. toggle_use_cases: monitored_rollout
# .. toggle_creation_date: 2019-09-24
# .. toggle_expiration_date: ??
# .. toggle_warnings: None
# .. toggle_tickets: PROD-62
# .. toggle_status: supported
ENABLE_VIDEO_URL_REWRITE = CourseWaffleFlag(
    waffle_namespace=COURSE_BLOCKS_API_NAMESPACE,
    flag_name="enable_video_url_rewrite",
    flag_undefined_default=True
)
