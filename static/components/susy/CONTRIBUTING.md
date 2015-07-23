Contributing to Susy
====================

Susy exists because of people contributing
ideas, code, issues, and sites.
Have you built a [site using Susy](http://susy.oddbird.net/sites-using-susy/)?
[Add it to the list](https://github.com/ericam/susysite/tree/master/content/sites-using-susy.rst).


Having issues?
--------------

First, try searching for similar questions/answers
that are already online.
If you don't see anything,
let us know.
We're always happy to help!

If it looks like a bug,
post it in the [GitHub issue tracker](https://github.com/ericam/susy/issues).
If you're just looking for advice
on creative uses of Susy,
maybe [Stack Overflow](http://stackoverflow.com/questions/tagged/susy-sass)
is the place for you.

Don't worry,
we'll field questions posted in either locations.
Make sure you explain the context around your problem
with code examples, screenshots,
or other relevant details.
Best if you can provide a simple code sample
that recreates the bug consistently.
The more you tell us,
and the more specific you are,
the better we can help.


Have an idea?
-------------

Susy wouldn't exist in it's current form,
without the ideas and feature requests
that people have sent in.
If you want to do something,
and don't see a good way to do it,
[please tell us](https://github.com/ericam/susy/issues)


Fix a bug or typo?
------------------

Thanks!
Submit a pull request against the `master` branch,
and we'll take a look.
If you think it might affect the tests,
or change functionality in some way,
see below.


Code a new feature?
-------------------

We love getting pull requests from the community.
If you have some code, please send us a pull request.
It's likely that we'll ask for a few adjustments,
but don't take it personally —
we often do that to each other as well.

We use [Compass](http://compass-style.org)
and [True](http://ericsuzanne.com/true) in development,
managed through [bundler](http://bundler.io/),
to test Susy and make sure everything is working properly.

We wont merge a pull request that breaks the test,
or adds a feature that is untested,
but you are welcome to submit a work in progress,
and we'll help you sort out the details.
We'll also ask you to update the docs.

When submitting a pull request, consider:
- Make sure the tests are up to date and passing
- Update the docs
- Add your changes to the
  [changelog](https://github.com/ericam/susy/blob/master/docs/changelog.rst).


Documentation
-------------

The docs are written as reStructuredText
([rst](http://docutils.sourceforge.net/rst.html)),
and built with [sphinx](http://sphinx-doc.org/).

To build them locally:

```bash
cd docs
pip install -r requirements.txt
make html
```

The docs are built into the `_build` directory,
as a static site you can open in your browser.


Running tests:
--------------

```bash
# command line
gem install bundler
rake test
```

You can also run `compass watch` from the test directory
if you want the tests running in the background while you work.
