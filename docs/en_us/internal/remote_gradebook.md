Grades can be pushed to a remote gradebook, and course enrollment membership can be pulled from a remote gradebook.  This file documents how to setup such a remote gradebook, and what the API should be for writing new remote gradebook "xservers".

1. Definitions

An "xserver" is a web-based server that is part of the edX ecosystem.  There are a number of "xserver" programs, including one which does python code grading, an xqueue server, and graders for other coding languages.

"Stellar" is the MIT on-campus gradebook system.

2. Setup

The remote gradebook xserver should be specified in the lms.envs configuration using

    FEATURES[REMOTE_GRADEBOOK_URL]

Each course, in addition, should define the name of the gradebook being used.  A class "section" may also be specified.  This goes in the policy.json file, eg:

    "remote_gradebook": {
       "name" : "STELLAR:/project/edxdemosite",
       "section" : "r01"
        },

3. The API for the remote gradebook xserver is an almost RESTful service model, which only employs POSTs, to the xserver url, with form data for the fields:

 - submit: get-assignments, get-membership, post-grades, or get-sections
 - gradebook: name of gradebook
 - user: username of staff person initiating the request (for logging)
 - section: (optional) name of section

The return body content should be a JSON string, of the format {'msg': message, 'data': data}.  The message is displayed in the instructor dashboard.

The data is a list of dicts (associative arrays).  Each dict should be key:value.

## For submit=post-grades:

A file is also posted, with the field name "datafile".  This file is CSV format, with two columns, one being "External email" and the other being the name of the assignment (that column contains the grades for the assignment).

## For submit=get-assignments

data keys = "AssignmentName"

## For submit=get-membership

data keys = "email", "name", "section"

## For submit=get-sections

data keys = "SectionName"
