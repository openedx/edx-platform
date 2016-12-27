# Analytics API endpoints

## Authentication
The API requires OAuth authentication to grant access to the endpoints and actions.

All endpoints can return the following response errors if there are problems with the authentication process:

### Credentials not provided
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Authentication credentials were not provided." }`
* Reason: Authentication credentials were not provided.

### Invalid Token
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Invalid Token." }`
* Reason: Invalid OAuth Token.

## Accounts

This endpoint provides information about user accounts. Can be called with filters for start date and end date, or can be called without parameters in order to get information for all registered accounts.

* URL: `api/jitterbit/v1/accounts/batch`
* Method: `GET`
* Optional URL Params:
	* `updated_min` (YYYY-MM-DD) Start date
	* `updated_max` (YYYY-MM-DD) End date

* Success Response
	* Code: 200
	* Content:
	```
	  {
    "username": "anewuser",
    "date_joined": "2016-12-17T23:45:47Z",
    "is_active": true,
    "id": 29,
    "email": "anewuser@example.com"
  },
  {
    "username": "newtest",
    "date_joined": "2016-12-17T23:55:27.765Z",
    "is_active": true,
    "id": 30,
    "email": "newtest@example.com"
  },
  ...
 	```
* 	Example calls:
	* `/api/jitterbit/v1/accounts/batch` All data of all users
	* `/api/jitterbit/v1/accounts/batch?updated_min=2015-12-09T00:00:00Z` Get data on users created after Dec 9th 2015
	* `/v1/accounts/batch?updated_min=2015-12-09T00:00:00Z&updated_max=2015-12-19` Get data on users created between Dec 9th and 19th 2015

## Enrollments

This endpoint provides information about course enrollment. Can be called with filters for course, start date, and end date, or can be called without parameters to get information for all enrollments.

* URL: `api/jitterbit/v1/enrollment/batch`
* Method: `GET`
* Optional URL Params:
	* `course_id` (course-v1:Org+Course+Run)
	* `updated_min` (YYYY-MM-DD) Start date
	* `updated_max` (YYYY-MM-DD) End date

* Success Response
	* Code: 200
	* Content:
	```
	[
  {
    "username": "honor",
    "course_id": "course-v1:edX+DemoX+Demo_Course",
    "user_id": 2,
    "enrollment_id": 1,
    "date_enrolled": "2016-05-23T16:17:07.585Z"
  },
  {
    "username": "audit",
    "course_id": "course-v1:edX+DemoX+Demo_Course",
    "user_id": 3,
    "enrollment_id": 2,
    "date_enrolled": "2016-05-23T16:17:11.068Z"
  },
  ...
  ]
	```

* 	Example calls:
	* `/api/jitterbit/v1/enrollment/batch` Get all course enrollments
	* `/api/jitterbit/v1/enrollment/batch?course_id=course-v1%3Aedx%2BDemoX101%2B2017` Get all course enrollments for edX DemoX Course
	* `/api/jitterbit/v1/enrollment/batch?course_id=course-v1%3Aedx%2BDemoX101%2B2017&update_min=2016-01-07` Get all course enrollments for Food Safety 101 enrolled after Jan 7th 2016:
