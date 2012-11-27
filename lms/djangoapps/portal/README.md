## acceptance_testing

This fake django app is here to support acceptance testing using <a href="http://lettuce.it/">lettuce</a> + 
<a href="https://github.com/wieden-kennedy/salad">salad</a> 
(which uses <a href="http://splinter.cobrateam.info/">splinter</a> wrapping <a href="http://selenium.googlecode.com/svn/trunk/docs/api/py/index.html">selenium</a>). 

Some documentation for our efforts are located in basecamp at <a href="https://basecamp.com/1892446/projects/841513-release/documents/1015202-staging-tests">this link</a>.

First you need to make sure that you've installed the requirements. 
This includes lettuce, salad, selenium, splinter, etc.
Do this with:
```pip install -r test-requirements.txt```

First set up the database that you need:
WARNING!!! THIS WILL OVERWRITE THE DATA IN YOUR DEV DATABASE
IF YOU WANT TO KEEP THAT DATA, SAVE A COPY OF YOUR ../db/mitx.db ELSEWHERE FIRST!

<li>If necessary, delete it first from mit_all/db</li>
<li>```rake django-admin[syncdb,lms,acceptance]```</li>
<li>```rake django-admin[migrate,lms,acceptance]```</li>

To use, start up the server separately:
```rake lms[acceptance]```

In between scenarios, flush the database with this command.
You will not need to do this if it's set up in the terrain.py file 
which is at the mitx root level.
```rake django-admin[flush,lms,acceptance,--noinput]```

Running the all the user acceptance scenarios:
```django-admin.py harvest --no-server --settings=lms.envs.acceptance --pythonpath=.```

Running a single user acceptance scenario:
```django-admin.py harvest --no-server --settings=lms.envs.acceptance --pythonpath=. lms/djangoapps/portal/features/signup.feature```

Or you can use the rake task named lettuce like this:
rake lettuce[lms/djangoapps/portal/features/homepage.feature]
