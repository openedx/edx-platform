## acceptance_testing

This fake django app is here to support acceptance testing using lettuce + selenium. Some documentation for our efforts are located in basecamp: https://basecamp.com/1892446/projects/841513-release/documents/1015202-staging-tests

You need to start the server first

Running all lettuce tests

```django-admin.py harvest --settings=lms.envs.acceptance_testing --pythonpath=. --no-server```

Running a single lettuce feature

```django-admin.py harvest --settings=lms.envs.acceptance_testing --pythonpath=. --no-server lms/djangoapps/acceptance_testing/features/homepage.feature```
