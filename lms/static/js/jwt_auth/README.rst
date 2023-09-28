Responsibilities
================
The code in the jwt_auth folder was pulled from https://github.com/openedx/frontend-platform/tree/master/src/auth

Primarily the code required to use https://github.com/openedx/frontend-platform/blob/master/src/auth/AxiosJwtTokenService.js

This code will require updates if changes are made in the AxiosJwtTokenService.

The responsibility of this code is to refresh and manage the JWT authentication token.
It is included in all of our Micro Front-ends (MFE), but in edx-platform course
dashboard and other frontend locations that are not yet in MFE form we still
need to update the token to be able to call APIs in other IDAs.

TODO: Investigate a long term approach to the JWT refresh issue in LMS https://openedx.atlassian.net/browse/MICROBA-548
