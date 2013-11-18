# edx-api

## Overview

**edx-api** is a MVP API contract to support the development of a MVP Mobile Application.
This API will only support the following use cases

- Signup
- Login
- Enroll/Unenroll in course
- Get list of enrolled courses

The amount of data returned to the client will be restricted to only contain information for these use cases. For example, the "get course navigational items" method will not - say - return due dates or gradable related information.

This document is a design document and will not delve into the implementation of this API contract

## HTTP Headers

There are two HTTP headers that are defined in the API contract:

| header | value |
| ------ | ----- |
| **X-edx-api-key** | shared secret between client and server. This identifies the calling software |
| **Authorization** | Bearer <access-token> |

This API will use OAuth2 for authentication. The access token reflects the OAuth2 token that will be returned when calling 'access_token' method (see below).


## General Notes
Unauthenticated access will return a HTTP 403 status code. All successful API calls will return HTTP Status code 200. Errors will return a different status code that will be documented for each method.

## Functional Endpoints

### Authentication

The following methods are related to user identity and authentication. These only support authentication against the Django-based user database.

##### Signup

**Request: HTTPS POST /edx-api/signup/v1/register**


```
application/json
{
	"email": "foo@bar.com",
	"username": "foobar",
	"full_name": "Foo Bar",
	"password": "password"
}
```

**Response: Success**

```
StatusCode: 200
application/json
{
	"token": "…securitytoken…"
}
```

**Response: Missing Parameter**

```
StatusCode: 400
application/json
{
	"err_type": "MissingParameter",
	"err_msg": "Missing required parameters"
}
```

**Response: User Already Exists**

```
StatusCode: 500
application/json
{
	"err_type": "UserAlreadyExists",
	"err_msg": "User Already Exists"
}
```

**Response: Invalid Email**

```
StatusCode: 500
application/json
{
	"err_type": "InvalidEmail",
	"err_msg": "Email provided is invalid"
}
```

**Response: Invalid Password**

```
StatusCode: 500
application/json
{
	"err_type": "InvalidPassword",
	"err_msg": "Password provided is invalid"
}
```

##### Login

This uses the OAuth2 provider for Django (django-oauth2-provider). As such it uses a slightly different HTTP POST Body format (application/x-www-form-urlencoded rather than JSON)

**Request: HTTPS POST /edx-api/auth/v1/access_token**

```
application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&grant_type=password&username=YOUR_USERNAME&password=YOUR_PASSWORD
```

**Response: success**

```
StatusCode: 200
application/json
{
	"access_token": "<your-access-token>", 
	"scope": "read", 
	"expires_in": 86399, 
	"refresh_token": "<your-refresh-token>"
}
```

**Response: Invalid email or password**

```
StatusCode: 500
application/json
{
	"err_type": "InvalidEmailPassword"
	"err_msg": "Invalid email or password"
}
```


##### Logout

**Request: HTTPS GET /edx-api/auth/v1/logout**

Note: Requires authentication token passed in the headers as indicated above

Response:

```
StatusCode: 200
```

### Registrar

The methods below expose functionality regarding enrollment in courses


##### Enroll in Course

**Request: HTTPS POST /edx-api/enrollment/v1/enroll**

Note: Requires authentication token passed in the headers as indicated above

```
application/json
{
	"course_id": "foo/bar/2013_Spring"
}
```

**Response: success**

```
StatusCode: 200
```

**Response: Course does not exist**

```
StatusCode: 500
application/json
{
	"err_type": "CourseDoesNotExist"
	"err_msg": "Course does not exist"
}
```

##### Unenroll in Course

**Request: HTTPS POST /edx-api/registrar/v1/unenroll**

Note: Requires authentication token passed in the headers as indicated above

```
application/json
{
	"course_id": "foo/bar/2013_Spring"
}
```

**Response: User not enrolled**

```
StatusCode: 500
application/json
{
	"err_type": "UserNotEnrolled"
	"err_msg": "User is not enrolled in course"
}
```

##### Get list of enrolled courses for user

**Request: HTTPS GET /edx-api/registrar/v1/get_enrollments_for_user**

Note: Requires authentication token passed in the headers as indicated above

**Response: success**

```
StatusCode: 200
application/json
{
	"enrollments": [
		{
			"course_id": "foo/bar/2013_Spring",
			"display_name": "Course Name",
			"display_org": "Foo",
			"display_coursenum": "Bar",
			"start": "2013-11-12",
			"course_image_url": "http://..."
		},
		...
	]
}
```

### Courseware

The following methods involve accessing the courseware database which is stored in MongoDB

##### Get list of courses

**Request: HTTPS GET /edx-mobile-api/v1/courseware/get_all_courses**

Note: Requires authentication token passed in the headers as indicated above

**Response: success**

```
StatusCode: 200
application/json
{
	"status": "success",
	"courses": [
		{
			"course_id": "foo/bar/2013_Spring",
			"display_name": "Course Name",
			"display_org": "Foo",
			"display_coursenum": "Bar",
			"start": "2013-11-12",
			"advertised_start": "2013-11-12"
			"short_description": "This is the small course description that normally appears in course catalog",
			"course_image_url": "http://...",
			"marketing_video_url": "http://..."
		},
		...
	]
}
```

##### Get course navigational elements

This method will return all non-leaf nodes in a course tree, e.g. Course, Chapters, Sections, Subsections.

**Request: HTTPS GET /edx-mobile-api/v1/courseware/get_course_navigation**

Note: Requires authentication token passed in the headers as indicated above

**Response: success**

```
StatusCode: 200
application/json
{
	"status": "success",
	"course": {
		"location": "i4x://foo/bar/course/2013_Spring"
		"display_name": "Foo Bar Course",
		"start": "2013-11-12",
		"children": [
			{
				"location": "i4x://foo/bar/chapter/chapter1",
				"display_name": "Chapter 1",
				"start": "2013-11-12",
				"children": [
					{
						"location": "i4x://foo/bar/sequential/seq1",
						"display_name": "First Sequence",
						"start": "2013-11-12",
						"children": [...]
					}
					...
				]
			},
			...
		]
	}
}
```

**Response: not enrolled in course**

HTTP Status code 403

##### Get course video elements

This method will return all videos within a course

**Request: HTTPS GET /edx-mobile-api/v1/courseware/get_course_videos**

Note: Requires authentication token passed in the headers as indicated above

**Response: success**

```
StatusCode: 200
application/json
{
	"status": "success",
	"course_videos": [
		{
			"parent_location": "i4x://foo/bar/vertical/vert1",
			"display_name": "Demo Video",
			"transcript_url": "http://...",
			"sources": {
				"youtube": {
					"1.0": "youtubeid",
					"0.75": "youtubeid",
					"1.25": "youtubeid",
					"2.0": "youtubeid"
				},
				"alt": { [
					"http://...",
					"http://..."
				]}
			}
		},
		...
	]
}
```