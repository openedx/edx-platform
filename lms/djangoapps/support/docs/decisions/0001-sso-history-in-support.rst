1. Registering SSO History Model in Support
================================================

Status
------

Accepted

Context
-------

SSO History was one of the feature requested by support that provides the 
historical data of any particular SSO record (based on UserSocialAuth)
in tools UI via support API. This SSO History can be utilized to track id changes,
Additional data or any other relevant data changes inside SSO model.

Although the UserSocialAuth is applied within common apps but is not configured for
cms. This has caused major breakage and a temporary outage in the authentication flow
in cms stage. 

Decision
--------

The simple_django_history registration for UserSocialAuth model 
is introduced in the Support app for LMS instead of the 
third_party_auth in Common. 

Consequences
------------

The most optimum method to introduce the feature was to register the model
in support app and get the data via support API.

Alternative/Rejected Approaches
------------

Addition for third_party_auth was attempted for the studio,
but failed in the stage. The primary reason was the failing migration 
tests in CMS with the current configurations in the studio. 
We tried to add the third_party_auth as an installed app on Studio 
but later found out that Studio is not configured for third_party_auth
and configuring third_party_auth on studio would have caused auth issues. 
Consequently, there was over 6 hours of pipeline outage on stage 
and we had to revert the changes made in the system.

Third party auth is primarily LMS-only app but since it has been in common, 
we opted to go ahead with adding history in common, 
only to later realize the impact of enabling third party auth in studio.
