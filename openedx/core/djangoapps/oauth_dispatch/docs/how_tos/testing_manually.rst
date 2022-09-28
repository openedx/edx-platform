Manually Testing OAuth2 Provider implementation
-----------------------------------------------

This document explains how to manually test the open edX LMS' OAuth2 Provider
implementation. In order to verify that it correctly implements the
`OAuth2 standard`_, use a publicly available 3rd party standard OAuth2 client.
The steps here show how to use `Google's OAuth2 Playground`_ as the client for
testing the `Authorization Code grant type`_. However, similar steps can be used
to test other grant types if they are substituted in the appropriate places.

1. Create an OAuth2 (DOT) Application in the LMS.

   i. Create or decide which LMS user will be associated with the OAuth2 application. In production, the user should be a "service user" that is distinct from "LMS end-users" that login to the system.

   ii. Go to http://localhost:18000/admin/oauth2_provider/application/add/ to create a new Application.

   iii. Enter a value for the "Name" field - a documentary value that uniquely describes this OAuth2 Application.

   iv. Enter a value for the "User" field - from Step 1i.

   v. Fill in the following required fields for the Authorization Code grant type:

      - Authorization grant type: Authorization code
      - Client type: Confidential
      - Redirect uris: https://developers.google.com/oauthplayground

   vi. The "Client id" and "Client secret" values are automatically randomly generated. You will later need these values in Step 4(iii) below to provide to the OAuth2 client.

   vii. Keep the "Skip authorization" checkbox deselected in order to test the interstitial approval form in the Authorization Code protocol.

   viii. Click Save.

2. Optional. Make the new Application a `Restricted Application`_ if you are testing Restricted Application features.

   i. Go to http://localhost:18000/admin/oauth_dispatch/restrictedapplication/add/

   ii. Find and select the new Application you created in the dropdown.

   iii. Click Save.

3. Create a publicly accessible URL to the LMS if you are testing on devstack. This step is needed to support the redirecting handshake in the Authorization Code protocol from Google's server back to localhost.

   i. Install `localtunnel`_:

        npm install -g localtunnel

   ii. Run localtunnel so it assigns a unique external url that proxies requests to the LMS on localhost:

        lt --port 18000

   iii. Copy the URL displayed in the terminal as you'll need it in Step 4(iii) to provide to the OAuth2 client.

4. Configure Google's OAuth2 Playground

   i. Go to https://developers.google.com/oauthplayground

   ii. Click on the settings wheel on the right to configure the OAuth2 client.

   iii. Enter the following values:

        - OAuth flow: Server-side
        - OAuth endpoints: custom
        - Authorization endpoint: <URL_FROM_STEP_3(iii)>/oauth2/authorize/
        - Token endpoint: <URL_FROM_STEP_3(iii)>/oauth2/access_token/
        - Access token location: Authorization header w/ Bearer prefix
        - Access type: Online
        - Force prompt: Consent screen
        - OAuth Client ID: <VALUE_FROM_STEP_1(vi)>
        - OAuth Client secret: <VALUE_FROM_STEP_1(vi)>

        .. image:: ../images/oauth_playground_config.png

   iv. Click "Close".

5. Initiate OAuth2 Authorization Code flow

   i. Go to Step 1 on the left side of the OAuth2 Playground.

   ii. In the "Input your own scopes" box, enter space-delimited requested scopes:

       .. image:: ../images/oauth_playground_scopes.png

   iii. Click the "Authorize APIs" button to initiate the OAuth2 Authorization Code protocol.

   iv. Follow through any interstitial steps that are required. Specifically,

       - If you aren't already logged in as an end-user on the LMS instance, you will be prompted to do so.

       - If that LMS end-user hasn't already approved the requested scopes for the OAuth2 Application, then you will be prompted to do so.

       - Once these interstitials are completed, the LMS will redirect back to the OAuth2 client (playground), assuming the redirect URL was correctly entered in Step 1(v).

       - If successful, the LMS would have responded back to the OAuth2 client with a temporary Authorization Code.

6. Exchange the Authorization Code for an Access Token.

   i. Go to Step 2 on the left side of the OAuth2 Playground. You will notice a random value in the "Authorization code" field, which was returned back by the LMS.

      .. image:: ../images/oauth_playground_step2.png

   ii. Click on the "Exchange authorization code for tokens" button.

   iii. Note: the Authorization Code is temporary and short-lived.

   iv. If successful, the LMS would have responded with a "Refresh token" and an "Access token".

       .. image:: ../images/oauth_playground_tokens.png

7. Call an LMS API with the Access Token.

   i. Go to Step 3 on the left side of the OAuth2 Playground. In the Request URI field, enter any LMS URL that supports OAuth2 authentication. Remember the base URL should be the URL from Step 3(iii).

      .. image:: ../images/oauth_playground_request_uri.png

   ii. Click on the "Send the request" button.

   iii. Verify the LMS response on the right side of the OAuth2 Playground.


.. _OAuth2 standard: https://tools.ietf.org/html/rfc6749
.. _Google's OAuth2 Playground: https://developers.google.com/oauthplayground
.. _Authorization Code grant type: https://tools.ietf.org/html/rfc6749#section-4.1
.. _Restricted Application: https://github.com/openedx/edx-platform/blob/dd136b457bc8a25892445fc4362ce02838179472/openedx/core/djangoapps/oauth_dispatch/models.py#L12
.. _localtunnel: https://localtunnel.github.io/www/
