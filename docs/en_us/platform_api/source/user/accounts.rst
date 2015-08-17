.. _User Accounts API:

##################################################
User Accounts API
##################################################

This page contains information on using the User Accounts API to
complete the following actions.

* `Get and Update the User's Account Information`_

.. _Get and Update the User's Account Information:

**********************************************
Get and Update the User's Account Information
**********************************************

.. .. autoclass:: user_api.accounts.views.AccountView

**Use Cases**

Get or update a user's account information. Updates are supported only through
merge patch.

**Example Requests**:

GET /api/user/v1/accounts/{username}/[?view=shared]

PATCH /api/user/v1/accounts/{username}/{"key":"value"} "application/merge-patch+json"

**Response Values for GET**

If the user makes the request for her own account, or makes a request for
another account and has "is_staff" access, the response contains:

* username: The username associated with the account.

* name: The full name of the user.

* email: email for the user (the new email address must be confirmed via a
  confirmation email, so GET will not reflect the change until the address has
  been confirmed).

* date_joined: The date the account was created, in the string format provided
  by datetime. For example, "2014-08-26T17:52:11Z".

* gender: One of the following values:
  * "m"
  * "f"
  * "o"
  * null

* year_of_birth: The year the user was born, as an integer, or null.

* level_of_education: One of the following values:

  * "p": PhD or Doctorate
  * "m": Master's or professional degree
  * "b": Bachelor's degree
  * "a": Associate's degree
  * "hs": Secondary/high school
  * "jhs": Junior secondary/junior high/middle school
  * "el": Elementary/primary school
  * "none": None
  * "o": Other
  * null: The user did not enter a value.

* language: The user's preferred language, or null.

* country: null (not set), or a Country corresponding to one of the ISO 3166-1
  countries.

* country: A ISO 3166 country code or null.

* mailing_address: The textual representation of the user's mailing address, or
  null.

* goals: The textual representation of the user's goals, or null.

* bio: null or textural representation of user biographical information ("about
  me").

* is_active: boolean representation of whether a user is active.

* profile_image: JSON representation of a user's profile image information. The
  keys are: the user's profile image:
                
* "has_image": boolean indicating whether the user has a profile image.
                
* "image_url_*": absolute URL to various sizes of a user's profile image, where
  '*' matches a representation of the corresponding image size such as 'small',
  'medium', 'large', and 'full'. These are configurable via
  PROFILE_IMAGE_SIZES_MAP.

* requires_parental_consent: true if the user is a minor requiring parental
  consent.

* language_proficiencies: array of language preferences. Each preference is a
  JSON object with the following keys:
                    
* "code": string ISO 639-1 language code e.g. "en".

For all text fields, clients rendering the values should take care to HTML
escape them to avoid script injections, as the data is stored
exactly as specified. The intention is that plain text is
supported, not HTML.

If a user who does not have "is_staff" access requests account information for
a different user, only a subset of these fields is returned. The fields
returned depend on the configuration setting ACCOUNT_VISIBILITY_CONFIGURATION,
and the visibility preference of the user for whom data is requested.

Note that a user can view which account fields they have shared with other
users by requesting their own username and providing the url parameter
"view=shared".

If no user exists with the specified username, a 404 error is returned.

**Response Values for PATCH**

Users can only modify their own account information. If the requesting user
does not have username "username", this method will return with a status of 403
for staff access but a 404 for ordinary users to avoid leaking the existence of
the account.

If no user exists with the specified username, a 404 error is returned.

If "application/merge-patch+json" is not the specified content type, a 415
error is returned.

If the update could not be completed due to validation errors, this method
returns a 400 error with all error messages in the "field_errors" field of the
returned JSON.

If the update could not be completed due to a failure at the time of the
update, a 400 error is returned with specific errors in the returned JSON
collection.

If the update is successful, a 204 status is returned with no additional
content.

**Example response showing the user's account information**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS, PATCH

    {
      "username": "John", 
      "name": "John Doe", 
      "language": "", 
      "gender": "m", 
      "year_of_birth": 2007, 
      "level_of_education": "m", 
      "goals": "Professional Development", 
      "country": US, 
      "mailing_address": "406 Highland Ave., Somerville, MA 02144", 
      "email": "johndoe@company.com", 
      "date_joined": "2015-03-18T13:42:40Z"
    } 
