CONVERSATIONALIST = ('conversationalist', 'Conversationalist')
TEAM_PLAYER = ('team', 'Team player')

BADGE_ID_KEY = 'badge_id'
BADGES_KEY = 'badges'
COURSE_ID_KEY = 'course_id'
ROOM_ID_KEY = 'room_id'
TEAM_ID_KEY = 'team_id'
TEAM_ROOM_ID_KEY = 'team__room_id'
THRESHOLD_KEY = 'badge__threshold'

MY_BADGES_URL_NAME = 'my_badges'

BADGE_ASSIGNMENT_ERROR = 'Rollback assigned badges for {num_of} users in team {team_id}'
BADGE_NOT_FOUND_ERROR = 'There exists no badge with id {badge_id}'
BADGE_TYPE_ERROR = 'Cannot assign badge {badge_id} of unknown type {badge_type}'
FILTER_BADGES_ERROR = 'Unable to get badges for team {team_id}'
INVALID_COMMUNITY_ERROR = 'Cannot assign badge {badge_id} for invalid community {community_id}'
INVALID_TEAM_ERROR = 'Cannot assign badge {badge_id} for invalid team {community_id}'
TEAM_BADGE_ERROR = 'Cannot assign missing badges to user {user_id} in team {team_id}'
UNKNOWN_COURSE_ERROR = 'Cannot assign badge {badge_id} for team {community_id} in unknown course'
