# Custom Response Load Test

## Optional Installations

* [memcached](http://pypi.python.org/pypi/python-memcached/): Install this 
and make sure it is running, or the Capa problem will not cache results.

* [AppArmor](http://wiki.apparmor.net): Follow the instructions in
`common/lib/codejail/README` to set up the Python sandbox environment.
If you do not set up the sandbox, the tests will still execute code in the CustomResponse,
so you can still run the tests.

* [matplotlib](http://matplotlib.org): Multi-mechanize uses this to create graphs.


## Running the Tests

This test simulates student submissions for a custom response problem.

First, clear the cache:

   /etc/init.d/memcached restart 

Then, run the test:

    multimech-run custom_response

You can configure the parameters in `customresponse/config.cfg`,
and you can change the CustomResponse script and student submissions
in `customresponse/test_scripts/v_user.py`.

## Components Under Test

Components under test:

* Python sandbox (see `common/lib/codejail`), which uses `AppArmor`
* Caching (see `common/lib/capa/capa/safe_exec/`), which uses `memcache` in production

Components NOT under test:

* Django views
* `XModule`
* gunicorn

This allows us to avoid creating courses in mongo, logging in, using CSRF tokens,
and other inconveniences.  Instead, we create a capa problem (from the capa package),
pass it Django's memcache backend, and pass the problem student submissions.

Even though the test uses `capa.capa_problem.LoncapaProblem` directly,
the `capa` should not depend on Django.  For this reason, we put the
test in the `courseware` Django app.
