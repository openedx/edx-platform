============================
LinkedIn Integration for edX
============================

This package provides a Django application for use with the edX platform which 
allows users to post their earned certificates on their LinkedIn profiles.  All
functionality is currently provided via a command line interface intended to be 
used by a system administrator and called from other scripts.

Basic Flow
----------

The basic flow is as follows:

o A system administrator uses the 'linkedin_login' script to log in to LinkedIn
  as a user with email lookup access in the People API.  This provides an access
  token that can be used by the 'linkedin_findusers' script to check for users
  that have LinkedIn accounts.

o A system administrator (or cron job, etc...) runs the 'linkedin_findusers'
  script to query the LinkedIn People API, looking for users of edX which have
  accounts on LinkedIn.

o A system administrator (or cron job, etc...) runs the 'linkedin_mailusers'
  script.  This scripts finds all users with LinkedIn accounts who also have
  certificates they've earned which they haven't already been emailed about.  
  Users are then emailed links to add their certificates to their LinkedIn 
  accounts.

Configuration
-------------

To use this application, first add it to your `INSTALLED_APPS` setting in your
environment config::

    INSTALLED_APPS += ('linkedin',)

You will then also need to provide a new key in your settings, `LINKEDIN_API`,
which is a dictionary::

    LINKEDIN_API = {
        # Needed for API calls
        'CLIENT_ID': "FJkdfj93kf93",
        'CLIENT_SECRET': "FJ93oldj939rkfj39",
        'REDIRECT_URI': "http://my.org.foo",

        # Needed to generate certificate links
        'COMPANY_NAME': 'Foo',
        'COMPANY_ID': "1234567",

        # Needed for sending emails
        'EMAIL_FROM': "The Team <someone@org.foo>",
        'EMAIL_WHITELIST': set(['fred@bedrock.gov', 'barney@bedrock.gov'])
    }

`CLIENT_ID`, `CLIENT_SECRET`, and `REDIRECT_URI` all come from your registration
with LinkedIn for API access.  `CLIENT_ID` and `CLIENT_SECRET` will be provied 
to you by LinkedIn.  You will choose `REDIRECT_URI`, and it will be the URI 
users are directed to after handling the authorization flow for logging into 
LinkedIn and getting an access token.

`COMPANY_NAME` is the name of the LinkedIn profile for the company issuing the
certificate, e.g. 'edX'.  `COMPANY_ID` is the LinkedIn ID for the same profile.
This can be found in the URL for the company profile.  For exampled, edX's 
LinkedIn profile is found at the URL: http://www.linkedin.com/company/2746406
and their `COMPANY_ID` is 2746406.

`EMAIL_FROM` just sets the from address that is used for generated emails.  

`EMAIL_WHITELIST` is optional and intended for use in testing.  If 
`EMAIL_WHITELIST` is given, only users whose email is in the whitelest will get
notification emails.  All others will be skipped.  Do not provide this in 
production.

If you are adding this application to an already running instance of edX, you
will need to use the `syncdb` script to add the tables used by this application
to the database.

Logging into LinkedIn
---------------------

The management script, `linkedin_login`, interactively guides a user to log into
LinkedIn and obtain an access token.  The script generates an authorization URL,
asks the user go to that URL in their web browser and log in via LinkedIn's web
UI.  When the user has done that, they will be redirected to the configured 
location with an authorization token embedded in the query string of the URL.  
This authorization token is good for only 30 seconds.  Within 30 seconds the 
user should copy and paste the URL they were directed to back into the command
line script, which will then obtain and store an access token.  

Access tokens are good for 60 days.  There is currently no way to refresh an
access token without rerunning the `linkedin_login` script again.

Finding Users
-------------

Once you have logged in, the management script, `linkedin_findusers`, is used
to find out which users have LinkedIn accounts using LinkedIn's People API.  By
default only users which have never been checked are checked.  The `--recheck`
option can be provided to recheck all users, in case some users have joined 
LinkedIn since the last time they were checked.

LinkedIn has provided guidance on what limits we should follow in accessing 
their API based on time of the day and day of the week.  The script attempts to
enforce that.  To override its enforcement, you can provide the `--force` flag.

Send Emails
-----------

Once you have found users, you can email them links for their earned 
certificates using the `linkedin_mailusers` script.  The script will only mail
any particular user once for any particular certificate they have earned.  

The emails come in two distinct flavors: triggered and grandfathered.  Triggered
emails are the default.  These comprise one email per earned certificate and are
intended for use when a user has recently earned a certificate, as will 
generally be the case if this script is run regularly.

The grandfathered from of the email can be sent by adding the `--grandfather`
flag and is intended to bring users up to speed with all of their earned 
certificates at once when this feature is first added to edX.  
