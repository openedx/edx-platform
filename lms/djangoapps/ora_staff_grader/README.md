# Enhanced Staff Grader (ESG) App

A backend-for-frontend (BFF) for ESG. It provides endpoints at the path `{lms-url}/api/ora_staff_grader/{endpoint}`.

ESG is an application on top of Open Response Assessments (ORA) designed to simplify staff grading of assignments. The BFF is designed to service the ESG microfrontend (MFE) by aggregating and packaging requests to both `edx-platform` and `edx-ora2`. 

The BFF includes both an API and mock API (/mock) for testing. Exercise either with the attached Postman collections (and included examples) or see [Enhanced Staff Grader Data Flow Design](https://openedx.atlassian.net/wiki/spaces/PT/pages/3154542730/Enhanced+Staff+Grader+Data+Flow+Design) for API reference.

## Quickstart

Connect to or exercise endpoints at `{lms-url}/api/ora_staff_grader/{endpoint}`.

Alternatively, use the attached postman collections to perform headless testing of endpoints. Following the setup below:

1. Perform headless login: in `lms.postman_collection.json` perform the `GET Login` call to generate a new CSRF token followed by a `POST Login` with valid staff credentials to authenticate with LMS.
2. Configure needed envirionment variables including `{{mock}} = False`
2. Exercise endpoints: in `ora_staff_grader.postman_collection.json`
