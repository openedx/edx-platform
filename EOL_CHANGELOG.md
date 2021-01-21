# Changelog EOL

## 21/01/2020 Changes on Certificates
- Get user profile name from user_certificate and not from user. (lms/djangoapps/certificates/views/webview.py)
- Update tests (lms/djangoapps/certificates/tests/test_webview_views.py)

## 09/10/2020 Changes on edx-proctoring
- Alert time remaining and show student progress (lms/templates/courseware/proctored-exam-status.underscore)

### 23/09/2020 Update send email message at instructor view
- Update success message. Append the email targets (lms/static/js/instructor_dashboard/send_email.js)

### 26/08/2020 Send email with *reply_to* attribute at instructor view
- New attribute on model *CourseEmail* (lms/djangoapps/bulk_email/models.py)
- Add *reply_to* attribute into *EmailMultiAlternatives()* (lms/djangoapps/bulk_email/tasks.py)
- Create *CourseEmail* with *reply_to* attribute from POST data (lms/djangoapps/instructor/views/api.py)
- Get *reply_to* value from the instructor view and send it by POST method (lms/static/js/instructor_dashboard/send_email.js)
- New tests (lms/djangoapps/bulk_email/tests/test_models_eol.py & lms/djangoapps/instructor/tests/test_api_eol.py)
