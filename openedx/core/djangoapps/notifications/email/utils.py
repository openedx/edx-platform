"""
Email Notifications Utils
"""
from django.conf import settings
from lms.djangoapps.branding.api import get_logo_url_for_email


def create_datetime_string(datetime_instance):
    return datetime_instance.strftime('%A, %b %d')


def get_icon_url_for_notification_type(notification_type):
    """
    Returns icon url for notification type
    """
    check_circle_green = "https://edx-notifications-static.edx.org/icons/check_circle_green.png"
    help_outline = "https://edx-notifications-static.edx.org/icons/help_outline.png"
    newspaper = "https://edx-notifications-static.edx.org/icons/newspaper.png"
    post_outline = "https://edx-notifications-static.edx.org/icons/post_outline.png"
    question_answer_outline = "https://edx-notifications-static.edx.org/icons/question_answer_outline.png"
    report_red = "https://edx-notifications-static.edx.org/icons/report_red.png"
    verified = "https://edx-notifications-static.edx.org/icons/verified.png"
    notification_type_dict = {
        "new_comment_on_response": question_answer_outline,
        "new_comment": question_answer_outline,
        "new_response": question_answer_outline,
        "new_discussion_post": post_outline,
        "new_question_post": help_outline,
        "response_on_followed_post": question_answer_outline,
        "comment_on_followed_post": question_answer_outline,
        "content_reported": report_red,
        "response_endorsed_on_thread": verified,
        "response_endorsed": check_circle_green,
        "course_update": newspaper,
    }
    return notification_type_dict.get(notification_type, post_outline)


def create_email_template_context():
    """
    Creates email context for header and footer
    """
    social_media_urls = settings.SOCIAL_MEDIA_FOOTER_ACE_URLS
    social_media_icons = settings.SOCIAL_MEDIA_LOGO_URLS
    social_media_info = {
        social_platform: {
            'url': social_media_urls[social_platform],
            'icon': social_media_icons[social_platform]
        }
        for social_platform in social_media_urls.keys()
        if social_media_icons.get(social_platform)
    }
    return {
        "platform_name": settings.PLATFORM_NAME,
        "logo_url": get_logo_url_for_email(),
        "social_media": social_media_info,
        "notification_settings_url": f"{settings.ACCOUNT_MICROFRONTEND_URL}/notifications",
    }


def create_email_digest_content(start_date, end_date=None, digest_frequency="Daily",
                                notifications_count=0, updates_count=0, email_content=None):
    """
    Creates email context based on content
    start_date: datetime instance
    end_date: datetime instance
    """
    context = create_email_template_context()
    start_date_str = create_datetime_string(start_date)
    end_date_str = create_datetime_string(end_date if end_date else start_date)
    context.update({
        "start_date": start_date_str,
        "end_date": end_date_str,
        "digest_frequency": digest_frequency,
        "updates": [
            {"count": updates_count, "type": "Updates"},
            {"count": notifications_count, "type": "Notifications"}
        ],
        "email_content": email_content if email_content else [],
        "get_icon_url_for_notification_type": get_icon_url_for_notification_type,
    })
    return context
