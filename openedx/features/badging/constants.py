"""
Constants for badging app
"""
CONVERSATIONALIST = ('conversationalist', 'Conversationalist')
TEAM_PLAYER = ('team', 'Team player')

BADGE_ID_KEY = 'badge_id'
BADGES_KEY = 'badges'
BADGES_DATE_EARNED_KEY = 'date_earned'
BADGES_PROGRESS_KEY = 'badge_progress'
COURSES_KEY = 'courses'
COURSE_ID_KEY = 'course_id'
COURSE_NAME_KEY = 'course__display_name'
COMMUNITY_URL_KEY = 'community_url'
DISCUSSION_ID_KEY = 'discussion_id'
DISCUSSION_COUNT_KEY = 'discussion_count'
POST_COUNT_KEY = 'post_count'
ROOM_ID_KEY = 'room_id'
TEAM_ID_KEY = 'team_id'
TEAM_COUNT_KEY = 'team_count'
TEAM_ROOM_ID_KEY = 'team__room_id'
THRESHOLD_KEY = 'badge__threshold'
THRESHOLD_LABEL_KEY = 'threshold'
USERNAME_KEY = 'username'

MY_BADGES_URL_NAME = 'my_badges'

BADGE_ASSIGNMENT_ERROR = 'Rollback assigned badges for {num_of} users in team {team_id}'
BADGE_NOT_FOUND_ERROR = 'There exists no badge with id {badge_id}'
BADGE_TYPE_ERROR = 'Cannot assign badge {badge_id} of unknown type {badge_type}'
FILTER_BADGES_ERROR = 'Unable to get badges for team {team_id}'
INVALID_COMMUNITY_ERROR = 'Cannot assign badge {badge_id} for invalid community {community_id}'
INVALID_TEAM_ERROR = 'Cannot assign badge {badge_id} for invalid team {community_id}'
TEAM_BADGE_ERROR = 'Cannot assign missing badges to user {user_id} in team {team_id}'
UNKNOWN_COURSE_ERROR = 'Cannot assign badge {badge_id} for team {community_id} in unknown course'

# philu notification type
EARNED_BADGE_NOTIFICATION_TYPE = 'philu.badging.user-badge-earned'
# philu notification renderer
JSON_NOTIFICATION_RENDERER = 'edx_notifications.renderers.basic.JsonRenderer'
