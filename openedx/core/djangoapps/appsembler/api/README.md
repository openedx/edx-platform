# Tahoe API

## Overview

This app serves Appsembler's REST API for Tahoe.


## API

### User Registration / Creation

Creates a new user. Used to provide invitation based sign-ups.

Endpoint: `/tahoe/api/v1/registrations/`

Request method: `POST`

Request body:

Required arguments (JSON data):

* "username"
* "email"
* "name"

Optional arguments:

* "password"
* "send_activation_email" - Flag value. Set to `true` or `false`. If omitted,
then defaults to `true`

Returns:
* HttpResponse: 200 on success, {"user_id ": 9}
* HttpResponse: 400 if the request is not valid.
* HttpResponse: 409 if an account with the given username or email address already exists

## Architecture

The Tahoe API is currently an embedded app in `edx-platform`.

* It generally follows the [standard Django reusable app structure][django-reusable-apps]
* It uses [Django REST Framework viewsets][drf-viewsets]
* DRF 'TokenAuthentication'
* edx-platform

The Tahoe API deviates from the standard Django app pattern in that it implements
a submodule (Python module) specific to the API version. This is to help maintainability
to support multiple API versions.

## Setup 

### Production

#### Production Setup

No additional configuration steps should be required (need to verify in
integration testing) to enable this api app.

#### Use

Token authentication is required. Each token is mapped to a user. The user
requires site admin permissions. See [Authentication](#authentication).

### Devstack

#### Devstack Setup

_This section contain rough notes that needs improvement_

For devstack, the environment needs to be set up for multiple sites.

##### Site setup

* Create at least one custom site
* Create an Organization for the custom site. Note the organization's short name
* Create a SiteConfiguration instance for the custom site
* Make sure the SiteConfiguration instance has 'course_org_filter' as one of
  the JSON data values and that this value is identical to the organization's
  short name.

##### User setup

To call the registration api in devstack, you will need to create a user who is
a site admin.

## Authentication

the Tahoe API uses token authentication. A token is mapped to a specific user.
Therefore to access the registration api, a token needs to be created for the user.

### How to create a token:

Open a shell to the server (or devstack) and become the `edxapp` user. Use the
api management command, `tahoe_create_token <username>` to create or get the
token for the user. Once a token has been created it will not change with
subsequent calls to this management command. To replace the token, for now you
will need to either remove it via the Django admin interface or from the Django
shell.

In the Django admin interface, go here: `admin/authtoken/token/`. This page
lets you manage tokens.

Alternately, you can delete the record directly from the token model given the
username.

```
from rest_framework.authtoken.models import Token
Token.objects.get(username='some_user').delete()

```

## Calling the API:

Add to the method header:

"Authorization: token <identifier>"


Example script to call the registration API:

```
#!/usr/bin/env python
"""
This script tests the Tahoe registration api.

To use this script, you'll need to:

1. Enable multiple sites and create a SiteConfiguration object for the site
   for which you are running this script
2. Create an AMC admin user token
3. Set the token to the "TAHOE_API_USER_KEY" environment variable
4. Set the host to the one in your dev environment in this script

For "2", you can use the Tahoe registration API management command,
"tahoe_create_token"

"""

import os
import pprint
import requests

import faker
import random

FAKE = faker.Faker()


host = 'http://alpha.localhost:8000'
api_url_root = host + '/tahoe/api/v1/'
reg_api_url = api_url_root + 'registrations/'


def generate_user_info():
    return dict(
        name=FAKE.name(),
        username=FAKE.user_name(),
        email=FAKE.email(),
        password=FAKE.password()
    )

def register_user(data):

    print('calling url:{} with data:'.format(reg_api_url))
    pprint.pprint(data)

    my_token = os.environ.get('TAHOE_API_USER_KEY')

    response = requests.post(
        reg_api_url,
        headers={'Authorization': 'Token {}'.format(my_token)},
        data=data)

    return response.json()


def main():
    # reg_data = dict(
    #     name='El Mo',
    #     username='elmo',
    #     email='elmo@example.com',
    #     password='bad-password',
    #     )

    reg_data = generate_user_info()

    print('Registering user:')
    pprint.pprint(reg_data)

    print('making call...')
    response_data = register_user(reg_data)
    print('response data:')
    pprint.pprint(response_data)


if __name__ == '__main__':
    main()

```

[django-reusable-apps]: https://docs.djangoproject.com/en/1.8/intro/reusable-apps/
[drf-viewsets]: https://www.django-rest-framework.org/api-guide/viewsets/
