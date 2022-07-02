# Mock Enhanced Staff Grader (ESG)

A mock backend-for-frontend (BFF) for ESG. It provides mocked endpoints at the path http(s)://{lms-url}/api/ora_staff_grader/mock/{endpoint}.

This is differentiated from the "real" BFF endpoints, which omit the `mock` part of the path. This should make it easy to switch between real/mocked versions by configuring the base API path.

The mock is, effectively, a wrapper on top of a JSON data store. All the important data is stored in the lms/djangoapps/ora_staff_grader/mock/data/ directory. Data is generally grouped by a key that would be supplied in the request (usually the submissionUUID and/or ora_location). To add/edit data, simply edit the underlying JSON files.

For some endpoints (e.g. lock/unlock/grade), there is simple interactivity; hitting the endpoint will save a change to the underlying data. These can be verified by reading the updated JSON files or reverted by doing a git checkout of the file.

## Quickstart

Connect to or exercise endpoints at `{devstack-url}/api/ora_staff_grader/mock/{endpoint}`.

Alternatively, use the attached postman collections to perform headless testing of endpoints. Following the setup below:

1. Perform headless login: in `lms.postman_collection.json` perform the `GET Login` call to generate a new CSRF token followed by a `POST Login` with valid credentials to authenticate with LMS.
2. Exercise mock endpoints: in `ora_staff_grader.postman_collection.json`, after configuring the environment variables including `{{mock}} = True`, run the example requests.

## API Reference

See [Enhanced Staff Grader Data Flow Design](https://openedx.atlassian.net/wiki/spaces/PT/pages/3154542730/Enhanced+Staff+Grader+Data+Flow+Design)
