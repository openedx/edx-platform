/* eslint-env node */
'use strict';

// By default, fixtures are loaded from spec/javascripts/fixtures but in karma everything gets served from /base
jasmine.getFixtures().fixturesPath = '/base/';

// https://github.com/edx/js-test-tool/blob/master/js_test_tool/templates/jasmine_test_runner.html#L10
// Stub out modal dialog alerts, which will prevent
// us from accessing the test results in the DOM
window.confirm = function() { return true; };
window.alert = function() { return; };
