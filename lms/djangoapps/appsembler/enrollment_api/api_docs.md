# Enrollment API endpoints

## Authentication
The API requires OAuth authentication for granting access to the endpoints and actions.

All endpoints can return the following response errors if there are problems with the authentication process:

### Credentials not provided
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Authentication credentials were not provided." }`
* Reason: Authentication credentials were not provided.

### Invalid Token
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Invalid Token." }`
* Reason: Invalid OAuth Token.

## Generate Enrollment Codes
This endpoint generates enrollment codes for a course. You can later enroll users in the course using the endpoint below and the  generated codes. This endpoint takes as parameters a course ID and the amount of desired codes to be generated.
More info about Enrollment Codes [edX Docs](http://edx.readthedocs.io/projects/open-edx-building-and-running-a-course/en/latest/manage_live_course/manage_course_fees.html#create-and-manage-enrollment-codes)

* URL: `/api/enrollment/v1/generate-codes`
* Method: `POST`
* Data Params
	* Required:
		* `course_id` (the course id `course-v1:Org+Code+Run`)
		* `total_registration_codes` (the amount of codes to generate and save)

* Success Response
	* Code: 200
	* Content:
```
{
  "course_id": "course-v1:edX+DemoX+Demo_Course",
  "codes": [
    "VQSG0xsg",
    "dWvbNXBT",
    "2z0rcZZs",
    "0Q6NvXFW",
    "xMc7SDJF"
  ],
  "course_url": "/courses/course-v1:edX+DemoX+Demo_Course/about"
}
```
* Example call:
```
POST /api/enrollment/v1/generate-codes
Host: example.com
Content-Type: application/json
Authorization: Bearer cbf6a5de322cf6a4323c957a882xy1s321c954b86
Cache-Control: no-cache
{
    "course_id": "course-v1:edX+DemoX+Demo_Course",
    "total_registration_codes": "20"
}
```

## Enroll User With Code
This endpoint allows you to enroll a user into a course using previously-generated Enrollment Codes. The endpoint takes as parameters the user email and the enrollment code.

* URL: `/api/enrollment/v1/enroll-user-with-code`
* Method: `POST`
* Data Params:
	* Required:
`email` (the user email)
`enrollment_code`: (the enrollment code obtained in the previous endpoint `/api/enrollment/v1/generate-codes`)
* Success Response:
	* Code: 200
	* Content:
```
{
  "success": "true",
}
```
* Error Responses:
	* Code: 400
	* Content: `{ "success": "false", "reason" : "Enrollment code error." }`
	* Reason: Enrollment code error.
**OR**
	* Code: 400
	* Content: `{ "success": "false", "reason" : "Enrollment code error." }`
	* Reason: Enrollment closed.
**OR**
	* Code: 400
	* Content: `{ "success": "false", "reason" : "Course full." }`
	* Reason: Course full.
**OR**
	* Code: 400
	* Content: `{ "success": "false", "reason" : "Already enrolled." }`
	* Reason: Already enrolled.

* Example call
```
POST /api/enrollment/v1/enroll-user-with-code
Host: example.com
Content-Type: application/json
Authorization: Bearer cbf6a5de322cf6a4323c957a882xy1s321c954b86
Cache-Control: no-cache
{
    "email": "staff@example.com",
    "enrollment_code": "V5QBQMN6"
}
```


## Enrollment Code Status
Via this endpoint the status of the Enrollment Codes can be changed. The endpoint takes as parameters the enrollment Code and the action (cancel or restore)

**cancel** When you can cancel an enrollment code, the code becomes unavailable. If a user was enrolled using this code, the user will be unenrolled from the related course.

**restore** If the code was previously "canceled", it will become available again. If the code was active and a user was enrolled in a course using it, the user will be unenrolled from the course, and the code will be available again for enrolling another user.

* URL: `api/enrollment/v1/enrollment-code-status`
* Method: `POST`
* Data Params:
	* Required:
`enrollment_code` (the enrollment code obtained in the previous endpoint `/api/enrollment/v1/generate-codes`)
`action`: ('cancel' or 'restore')
* Success Response:
	* Code: 200
	* Content: `{"success": "true"}`
* Error Responses:
	* Code: 400
	* Reason: `{ "success": "false", "reason" : "The enrollment code ({code}) was not found"}`
* Example call:
```
POST /api/enrollment/v1/enrollment-code-status
Host: example.com
Content-Type: application/json
Authorization: Bearer cbf6a5de322cf6a4323c957a882xy1s321c954b86
Cache-Control: no-cache
{
    "enrollment_code": "V5QBQMN6",
    "action": "restore"
}
```
**OR**
```
POST /api/enrollment/v1/enrollment-code-status
Host: example.com
Content-Type: application/json
Authorization: Bearer cbf6a5de322cf6a4323c957a882xy1s321c954b86
Cache-Control: no-cache
{
    "enrollment_code": "1Ls34dQa",
    "action": "cancel"
}
```
