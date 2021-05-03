"""
This app contains mandrill client and related tasks to send emails

Mandrill client depends on MANDRILL_API_KEY, otherwise tasks will raise exception. In unit test
it is recommended to mock client so that there is no external dependency on code which also means
MANDRILL_API_KEY will not be required in unit tests
"""
