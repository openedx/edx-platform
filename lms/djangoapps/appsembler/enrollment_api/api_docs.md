# Enrollment API endpoints

## Authentication
The API requires OAuth auth for grant access to the endpoints and actions.

All endpoints can return the following response errors if there some problem with the authentication process:
### Credentials not provided
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Authentication credentials were not provided." }`
* Reason: Authentication credentials were not provided.
### Invalid Token
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Invalid Token." }`
* Reason: Invalid OAuth Token.

## Generate Enrollment Codes
This endpoint generate enrollment codes for a course, you can later enroll users in the course using the endpoint bellow and the  generated codes. The endpoint receive for parameters a course ID and the amount of desired codes to be generated.
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
This endpoint allow to enrol an user into a course using previously generated Enrollment Codes. The endpoint receives as a parameters the user email and the enrollment code.

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
I this endpoint the status of the Enrollment Codes can be changed. The endpoint receives as a parameters the enrollment Code and the action (cancel or restore)
**cancel** When you can cancel a enrollment code, the code became unavailable, if a user was enrolled using this code, will be unenrolled from the course.
**restore** If the code was "canceled" will be available again. If code was active and a user was enrolled in a course using it, will be unenrolled from the course, and the code will be available again for to enroll another user.

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
