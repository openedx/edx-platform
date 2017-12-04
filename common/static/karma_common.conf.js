// Karma config for common suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

/* eslint-env node */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    useRequireJs: false,

    normalizePathsForCoverageFunc: function(appRoot, pattern) {
//        return path.join(appRoot, '/common/static/' + pattern);
        return path.join(appRoot, pattern);
    },

    // Avoid adding files to this list. Use RequireJS.
    libraryFilesToInclude: [
        {pattern: 'common/static/coffee/src/ajax_prefix.js', included: true},
        {pattern: 'common/static/js/vendor/draggabilly.js', included: true},
        {pattern: 'common/static/common/js/vendor/jquery.js', included: true},
        {pattern: 'common/static/common/js/vendor/jquery-migrate.js', included: true},
        {pattern: 'common/static/coffee/src/jquery.immediateDescendents.js', included: true},
        {pattern: 'common/static/js/vendor/jquery.leanModal.js', included: true},
        {pattern: 'common/static/js/vendor/jquery.timeago.js', included: true},
        {pattern: 'common/static/js/vendor/jquery.truncate.js', included: true},
        {pattern: 'common/static/js/vendor/URI.min.js', included: true},
        {pattern: 'common/static/js/test/add_ajax_prefix.js', included: true},
        {pattern: 'common/static/js/test/i18n.js', included: true},

        {pattern: 'common/static/common/js/vendor/underscore.js', included: true},
        {pattern: 'common/static/common/js/vendor/underscore.string.js', included: true},
        {pattern: 'common/static/common/js/vendor/backbone.js', included: true},

        {pattern: 'common/static/edx-ui-toolkit/js/utils/global-loader.js', included: true},
        {pattern: 'common/static/edx-ui-toolkit/js/utils/string-utils.js', included: true},
        {pattern: 'common/static/edx-ui-toolkit/js/utils/html-utils.js', included: true},

        {pattern: 'common/static/js/vendor/jasmine-imagediff.js', included: true},
        {pattern: 'common/static/common/js/spec_helpers/jasmine-extensions.js', included: true},
        {pattern: 'common/static/common/js/spec_helpers/jasmine-waituntil.js', included: true},
        {pattern: 'common/static/common/js/spec_helpers/discussion_spec_helper.js', included: true},
        {pattern: 'common/static/common/js/spec/discussion/view/discussion_view_spec_helper.js', included: true}
    ],

    libraryFiles: [
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        {pattern: 'common/static/coffee/src/**/*.js', included: true},
        {pattern: 'common/static/common/js/xblock/core.js', included: true},
        {pattern: 'common/static/common/js/xblock/runtime.v1.js', included: true},
        {pattern: 'common/static/common/js/discussion/**/*.js', included: true},
        {pattern: 'common/static/js/capa/src/**/*.js', included: true},
        {pattern: 'common/static/js/src/**/*.js', included: true}
    ],

    specFiles: [
        {pattern: 'common/static/coffee/spec/**/*.js', included: true},
        {pattern: 'common/static/common/js/spec/xblock/*.js', included: true},
        {pattern: 'common/static/common/js/spec/discussion/**/*spec.js', included: true},
        {pattern: 'common/static/js/**/*spec.js', included: true}
    ],

    fixtureFiles: [
        {pattern: 'common/static/js/fixtures/**/*.html'},
        {pattern: 'common/static/js/capa/fixtures/**/*.html'},
        {pattern: 'common/static/common/templates/**/*.underscore'}
    ]
};

module.exports = function(config) {
    configModule.configure(config, options);
};
