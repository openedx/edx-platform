# Testing

Testing is good.  Here is some useful info about how we set up tests--

### Backend code:

- TODO

### Frontend code:

We're using Jasmine to unit-testing the JavaScript files. All the specs are
written in CoffeeScript for the consistency. To access the test cases, start the
server in debug mode, navigate to `http://127.0.0.1:[port number]/_jasmine` to
see the test result.

All the JavaScript codes must have test coverage. Both CMS and LMS
has its own test directory in `{cms,lms}/static/coffee/spec`  If you haven't
written a JavaScript test before, you can look at those example files as a
starting point. Also, these materials might be helpful for you:

CMS Note: For consistency, you're advised to use the same directory structure
for implementation and test. For example, test for `src/views/module.coffee`
should be written in `spec/views/module_spec.coffee`.

* http://pivotal.github.com/jasmine
* http://railscasts.com/episodes/261-testing-javascript-with-jasmine?view=asciicast
* http://a-developer-life.blogspot.com/2011/05/jasmine-part-1-unit-testing-javascript.html

If you're finishing a feature that contains JavaScript code snippets and do not
sure how to test, please feel free to open up a pull request and asking people
for help. (However, the best way to do it would be writing your test first, then
implement your feature - Test Driven Development.)
