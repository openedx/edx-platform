# Template used to create cache keys for individual programs.
PROGRAM_CACHE_KEY_TPL = 'program-{uuid}'

# Cache key used to locate an item containing a list of all program UUIDs.
# This has to be deleted when removing the waffle flags populate-multitenant-programs and get-multitenant-programs
# For more, see LEARNER-1146
PROGRAM_UUIDS_CACHE_KEY = 'program-uuids'

# Cache key used to locate an item containing a list of all program UUIDs for a site.
SITE_PROGRAM_UUIDS_CACHE_KEY_TPL = 'program-uuids-{domain}'
