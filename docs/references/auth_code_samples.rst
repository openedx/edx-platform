Authentication Related Code Samples
###################################

.. warning::

   Access Tokens, Refresh Tokens and Client Secrets are generally considered
   secret and should not live in your code.  We print them here so that these
   examples are useful but you should generally not expose any of these tokens
   to systems or clients you don't trust.

.. _JWT from user:

Get a JWT with a Username and Password
**************************************

.. code-block::

   import requests
   from pprint import pprint

   token_request = requests.post(
       f"http://lms.example.com/oauth2/access_token",
       data={
           "client_id": "login-service-client-id",
           "grant_type": "password",
           "username": "test_user",
           "password": "test_password",
           "token_type": "JWT",
       },
   )
   pprint(token_request.json())

.. code-block::
   :caption: Output

   {'access_token': 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiAibG1zLWtleSIsICJleHAiOiAxNjkyMjExNjM4LCAiZ3JhbnRfdHlwZSI6ICJwYXNzd29yZCIsICJpYXQiOiAxNjkyMjA4MDM4LCAiaXNzIjogImh0dHA6Ly9sb2NhbGhvc3Q6MTgwMDAvb2F1dGgyIiwgInByZWZlcnJlZF91c2VybmFtZSI6ICJmZWFuaWwiLCAic2NvcGVzIjogWyJyZWFkIiwgIndyaXRlIiwgImVtYWlsIiwgInByb2ZpbGUiXSwgInZlcnNpb24iOiAiMS4yLjAiLCAic3ViIjogIjVjMTBmNjZmMmQ2MzkwYjcwNjYyYzkxNGFhZTdlZjc5IiwgImZpbHRlcnMiOiBbInVzZXI6bWUiXSwgImlzX3Jlc3RyaWN0ZWQiOiBmYWxzZSwgImVtYWlsX3ZlcmlmaWVkIjogdHJ1ZSwgImVtYWlsIjogImZlYW5pbEBheGltLm9yZyIsICJuYW1lIjogIkZlYW5pbCBQYXRlbCIsICJmYW1pbHlfbmFtZSI6ICIiLCAiZ2l2ZW5fbmFtZSI6ICIiLCAiYWRtaW5pc3RyYXRvciI6IHRydWUsICJzdXBlcnVzZXIiOiB0cnVlfQ.iGFl7qsAUau0-40oq8Of0f72kguq2Hc_drijCnI2I-M',
    'expires_in': 3600,
    'refresh_token': 'm8iXhVlGABu52xFxVFj5rAz8xSjsRq',
    'scope': 'read write email profile',
    'token_type': 'JWT'}

.. note:: The client type must be ``public`` for this to work.

.. _JWT from application:

Get a JWT with a client_id and client_secret
********************************************

.. code-block::

   import base64
   import requests

   from pprint import pprint

   client_id = "ukbclQB8aPh7hgsy8ifPXkPf7fRqgUq1w21f2YZa"
   # Note this should actually be secret and probably not in your code but
   # provided here in the example
   client_secret = "xkN0BJ19q9Jk8UPUppEtC1xe4764c81ioFtlegvokbmnAC7CFCT5gG1Og5nnFmCNc3NHNhUwWWDRVcBfnLSZ4xAlEmSePzfkFtLE06cwR1MuSc0gx9LUEjRrTs3j2vgK"

   credential = f"{client_id}:{client_secret}"
   encoded_credential = base64.b64encode(credential.encode("utf-8")).decode("utf-8")

   headers = {"Authorization": f"Basic {encoded_credential}", "Cache-Control": "no-cache"}
   data = {"grant_type": "client_credentials", "token_type": "jwt"}

   token_request = requests.post(
       "http://lms.example.com/oauth2/access_token", headers=headers, data=data
   )

   pprint(token_request.json())

.. code-block::
   :caption: Output

   {'access_token': 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiAibG1zLWtleSIsICJleHAiOiAxNjkyMjExNjM4LCAiZ3JhbnRfdHlwZSI6ICJjbGllbnQtY3JlZGVudGlhbHMiLCAiaWF0IjogMTY5MjIwODAzOCwgImlzcyI6ICJodHRwOi8vbG9jYWxob3N0OjE4MDAwL29hdXRoMiIsICJwcmVmZXJyZWRfdXNlcm5hbWUiOiAiZmVhbmlsIiwgInNjb3BlcyI6IFsicmVhZCIsICJ3cml0ZSIsICJlbWFpbCIsICJwcm9maWxlIl0sICJ2ZXJzaW9uIjogIjEuMi4wIiwgInN1YiI6ICI1YzEwZjY2ZjJkNjM5MGI3MDY2MmM5MTRhYWU3ZWY3OSIsICJmaWx0ZXJzIjogW10sICJpc19yZXN0cmljdGVkIjogZmFsc2UsICJlbWFpbF92ZXJpZmllZCI6IHRydWUsICJlbWFpbCI6ICJmZWFuaWxAYXhpbS5vcmciLCAibmFtZSI6ICJGZWFuaWwgUGF0ZWwiLCAiZmFtaWx5X25hbWUiOiAiIiwgImdpdmVuX25hbWUiOiAiIiwgImFkbWluaXN0cmF0b3IiOiB0cnVlLCAic3VwZXJ1c2VyIjogdHJ1ZX0.CX1S0QGrWKEPOHC8kUzGcvW8Ky04RCA8vU8WJrZURSw',
    'expires_in': 3600,
    'scope': 'read write email profile',
    'token_type': 'JWT'}

.. note:: When you get a JWT using ``client_credentials`` you don't get a
   refresh token.  You're just expected to make a new call with your client
   credentials.

Check to see if a JWT is Expired
********************************

.. code-block::

   import jwt

   # See above examples for how to get a JWT token
   jwt_token = token_request.json()['access_token']

   try:
       jwt.decode(jwt_token, "secret", audience="lms-key", algorithms=['HS256'])
   except jwt.ExpiredSignatureError:
       # Signature has expired

Refresh a JWT Using a Refresh Token
***********************************

.. code-block::

   import requests

   # See "Get a JWT with a Username and Password" for how to get a refresh token.
   # The response from that request will include a `refresh_token` attribute.
   refresh_token = token_request.json()['refresh_token']

   refreshed_token_request = requests.post(
       f"http://lms.example.com/oauth2/access_token",
       data={
           "client_id": "login-service-client-id",
           "grant_type": "refresh_token",
           "refresh_token": token_request.json()['refresh_token'],
           "token_type": "JWT",
       },
   )

   pprint(refreshed_token_request.json())

.. code-block::
   :caption: Output


   {'access_token': 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiAibG1zLWtleSIsICJleHAiOiAxNjkyMjE1MTgwLCAiZ3JhbnRfdHlwZSI6ICJwYXNzd29yZCIsICJpYXQiOiAxNjkyMjExNTgwLCAiaXNzIjogImh0dHA6Ly9sb2NhbGhvc3Q6MTgwMDAvb2F1dGgyIiwgInByZWZlcnJlZF91c2VybmFtZSI6ICJmZWFuaWwiLCAic2NvcGVzIjogWyJyZWFkIiwgIndyaXRlIiwgImVtYWlsIiwgInByb2ZpbGUiXSwgInZlcnNpb24iOiAiMS4yLjAiLCAic3ViIjogIjVjMTBmNjZmMmQ2MzkwYjcwNjYyYzkxNGFhZTdlZjc5IiwgImZpbHRlcnMiOiBbInVzZXI6bWUiXSwgImlzX3Jlc3RyaWN0ZWQiOiBmYWxzZSwgImVtYWlsX3ZlcmlmaWVkIjogdHJ1ZSwgImVtYWlsIjogImZlYW5pbEBheGltLm9yZyIsICJuYW1lIjogIkZlYW5pbCBQYXRlbCIsICJmYW1pbHlfbmFtZSI6ICIiLCAiZ2l2ZW5fbmFtZSI6ICIiLCAiYWRtaW5pc3RyYXRvciI6IHRydWUsICJzdXBlcnVzZXIiOiB0cnVlfQ.oNTEk7aMFSjvEbvH_-Gu2QZE93w-CpXSIIuN-IC6BSU',
    'expires_in': 3600,
    'token_type': 'JWT',
    'scope': 'read write email profile',
    'refresh_token': 'V5fbgDt2RPVnmI6Q3c6cJ3OjVriGii'}

Use a JWT Header to call an API
*******************************

.. code-block::

   # See above examples for how to get a JWT token
   access_token = token_request.json()["access_token"]

   enrollment_request = requests.get(
       "http://lms.example.com/api/enrollment/v1/enrollment",
       headers={"Authorization": f"JWT {access_token}"},
   )

   pprint(enrollment_request.json())

.. code-block::
   :caption: Output

   [{'course_details': {'course_end': None,
                        'course_id': 'course-v1:TestX+Course+1',
                        'course_modes': [{'bulk_sku': None,
                                          'currency': 'usd',
                                          'description': None,
                                          'expiration_datetime': None,
                                          'min_price': 0,
                                          'name': 'Audit',
                                          'sku': None,
                                          'slug': 'audit',
                                          'suggested_prices': ''}],
                        'course_name': 'Open edX Test Course',
                        'course_start': '2022-04-09T00:00:00Z',
                        'enrollment_end': None,
                        'enrollment_start': None,
                        'invite_only': False,
                        'pacing_type': 'Instructor Paced'},
     'created': '2023-08-17T14:10:48.476967Z',
     'is_active': True,
     'mode': 'audit',
     'user': 'test_user'}]
