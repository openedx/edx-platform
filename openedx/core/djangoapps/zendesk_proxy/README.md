# Zendesk API proxy endpoint

Introduced via [EDUCATOR-1889](https://openedx.atlassian.net/browse/EDUCATOR-1889)

### Purpose

This djangoapp contains no models, just a single view. The intended purpose is to provide a way for unauthenticated POST requests to create ZenDesk tickets. The reason we use this proxy instead of a direct POST is that it allows us to keep ZenDesk credentials private, and rotate them if needed. This proxy endpoint should be rate-limited to avoid abuse.
