# User API endpoints

## Authentication
The API requires OAuth authentication to grant access to the endpoints and actions.

All endpoints can return the following response errors if there some problem with the authentication process:

### Credentials not provided
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Authentication credentials were not provided." }`
* Reason: Authentication credentials were not provided.

### Invalid Token
* Code: 401 UNAUTHORIZED
* Content: `{ detail : "Invalid Token." }`
* Reason: Invalid OAuth Token.

## Create User Account

This endpoint creates a new edX user.

* URL: `/api/user_api/v1/accounts/create`
* Method: `POST`
* Data Params
	* Required:
		* 'username'
		* 'password'
		* 'email'
		* 'name'

* Success Response
	* Code: 200
	* Content:
```
{
	"user_id ": 65, # the id of the new user
}
```
* Error Responses:
	* Code: 400
	* Content: `{"user_message": "Wrong parameters on user creation"}`
	* Reason: Wrong parameters on user creation

	* Code: 409
	* Content: `{"user_message": "User already exists"}`
	* Reason: User already exists

* Example call:
```
POST /api/enrollment/v1/enrollment-code-status
Host: example.com
Content-Type: application/json
Authorization: Bearer cbf6a5de322cf6a4323c957a882xy1s321c954b86
Cache-Control: no-cache
{
	"username": "staff55",
    "password": "edx",
    "email": "staff55@example.com",
    "name": "stafftest"
}
```

## Check Existing Username

This endpoint is a tool to check if an user exists given the username.

* URL: `/api/user_api/v1/accounts/(?P<username>[\w.+-]+)`
* Method: `GET`

* Success Response
	* Code: 200
	* Content:
```
{
	"user_id ": "username",
}
```
* Error Responses:
	* Code: 404 NOT FOUND
	* Reason: User not exists
