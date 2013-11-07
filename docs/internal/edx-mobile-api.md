# edx-mobile-api

## Overview

**edx-mobile-api** is a specialized API contract to support the development of a MVP Mobile Application. This API will only support the following use cases

- Signup
- Login/Logout
- Enroll/Unenroll in course
- Get list of enrolled courses
- Get course catalog
- Get course navigational items
- Get course videos

The amount of data returned to the client will be restricted to only contain information for these use cases. For example, the "get course navigational items" method will not - say - return due dates or gradable related information.


This document is a design document and will not delve into the implementation of this API contract

## HTTP Headers

There are two HTTP headers that are defined in the API contract:

| header | value |
| ------ | ----- |
| **X-edx-api-key** | shared secret between client and server. This identifies the calling software |
| **X-edx-security-token** | security token returned from the auth endpoint |

The **X-edx-api-key** is required for all methods. The **X-edx-security-token** is required for all authenticated methods.

## General Notes
Unauthenticated access will return a HTTP 403 status code.

## Functional Endpoints

### Authentication

The following methods are related to user identity and authentication. These only support authentication against the Django-based user database.

##### Signup

**Request: HTTPS POST /edx-mobile-api/v1/auth/register**


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
	"status": "success",
	"token": "…securitytoken…"
}
```

**Response: Missing Parameter**

```
StatusCode: 400
application/json
{
	"status": "err",
	"err_type": "MissingParameter",
	"err_msg": "Missing required parameters"
}
```

**Response: User Already Exists**

```
StatusCode: 500
application/json
{
	"status": "err",
	"err_type": "UserAlreadyExists",
	"err_msg": "User Already Exists"
}
```

**Response: Invalid Email**

```
StatusCode: 500
application/json
{
	"status": "err",
	"err_type": "InvalidEmail",
	"err_msg": "Email provided is invalid"
}
```

**Response: Invalid Password**

```
StatusCode: 500
application/json
{
	"status": "err",
	"err_type": "InvalidPassword",
	"err_msg": "Password provided is invalid"
}
```

##### Login

**Request: HTTPS POST /edx-mobile-api/v1/auth/login**

```
application/json
{
	"email": "foo@bar.com",
	"password": "password"
}
```

**Response: success**

```
StatusCode: 200
application/json
{
	"status": "success",
	"token": "…securitytoken…"
}
```

**Response: Invalid email or password**

```
StatusCode: 500
application/json
{
	"status": "error",
	"err_type": "InvalidEmailPassword"
	"err_msg": "Invalid email or password"
}
```


##### Logout

**Request: HTTPS GET /edx-mobile-api/v1/auth/logout**

Note: Requires authentication token passed in the headers as indicated above

Response:

```
StatusCode: 200
application/json
{
	"status": "success"
}
```

### Registrar

The methods below expose functionality regarding enrollment in courses


##### Enroll in Course

**Request: HTTPS POST /edx-mobile-api/v1/registrar/enroll**

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
application/json
{
	"status": "success"
}
```

**Response: Course does not exist**

```
StatusCode: 500
application/json
{
	"status": "error",
	"err_type": "CourseDoesNotExist"
	"err_msg": "Course does not exist"
}
```

##### Unenroll in Course

**Request: HTTPS POST /edx-mobile-api/v1/registrar/unenroll**

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
	"status": "error",
	"err_type": "UserNotEnrolled"
	"err_msg": "User is not enrolled in course"
}
```

##### Get list of enrolled courses for user

**Request: HTTPS GET /edx-mobile-api/v1/registrar/get_enrollments_for_user**

Note: Requires authentication token passed in the headers as indicated above

**Response: success**

```
StatusCode: 200
application/json
{
	"status": "success",
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