## acceptance_testing

This fake django app is here to support acceptance testing using <a href="http://lettuce.it/">lettuce</a> + 
<a href="http://splinter.cobrateam.info/">splinter</a> (which wraps <a href="http://selenium.googlecode.com/svn/trunk/docs/api/py/index.html">selenium</a>).

First you need to make sure that you've installed the requirements. 
This includes lettuce, selenium, splinter, etc.
Do this with:
```pip install -r test-requirements.txt```

The settings.py environment file used is named acceptance.py.
It uses a test SQLite database defined as ../db/test-mitx.db.
You need to first start up the server separately, then run the lettuce scenarios.

Full documentation can be found on the wiki at <a href="https://edx-wiki.atlassian.net/wiki/display/ENG/Lettuce+Acceptance+Testing">this link</a>.
