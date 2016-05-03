// Karma config for lms suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFiles: [
        {pattern: 'xmodule_js/common_static/js/test/i18n.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js'},
        {pattern: 'xmodule_js/common_static/js/src/logger.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js'},
        {pattern: 'js/RequireJS-namespace-undefine.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/text.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.simulate.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.timeago.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/flot/jquery.flot.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/url.min.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js'},
        {pattern: 'xmodule_js/common_static/js/xblock/**/*.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/xblock/**/*.js'},
        {pattern: 'coffee/src/instructor_dashboard/**/*.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/sinon-1.17.0.js'},
        {pattern: 'xmodule_js/src/capa/**/*.js'},
        {pattern: 'xmodule_js/src/video/**/*.js'},
        {pattern: 'xmodule_js/src/xmodule.js'},
        {pattern: 'xmodule_js/common_static/js/src/**/*.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.string.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/backbone.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/backbone.paginator.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/edxnotes/annotator-full.min.js'},
        {pattern: 'xmodule_js/common_static/js/test/i18n.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/date.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/moment.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/moment-with-locales.min.js'},
        {pattern: 'xmodule_js/common_static/common/js/utils/edx.utils.validate.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.event.drag-2.2.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/slick.core.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/slick.grid.js', included: true},
        {pattern: 'xmodule_js/common_static/js/libs/jasmine-waituntil.js', included: true},
        {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true},
        {pattern: 'common/js/utils/require-serial.js', included: true}
    ],

    sourceFiles: [
        {pattern: 'js/**/!(*spec).js'},
        {pattern: 'coffee/src/**/*.js'},
        {pattern: 'common/js/**/*.js'},
        {pattern: 'edx-pattern-library/js/**/*.js'},
        {pattern: 'edx-ui-toolkit/js/**/*.js'},
        {pattern: 'support/js/**/!(*spec).js'},
        {pattern: 'teams/js/**/!(*spec).js'},
        {pattern: 'xmodule_js/common_static/coffee/**/*.js'}
    ],

    specFiles: [
        {pattern: 'js/spec/**/*spec.js'},
        {pattern: 'teams/js/spec/**/*spec.js'},
        {pattern: 'support/js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'js/fixtures/**/*.html'},
        {pattern: 'templates/instructor/instructor_dashboard_2/**/*.*'},
        {pattern: 'templates/dashboard/**/*.*'},
        {pattern: 'templates/edxnotes/**/*.*'},
        {pattern: 'templates/fields/**/*.*'},
        {pattern: 'templates/student_account/**/*.*'},
        {pattern: 'templates/student_profile/**/*.*'},
        {pattern: 'templates/verify_student/**/*.*'},
        {pattern: 'templates/file-upload.underscore'},
        {pattern: 'templates/components/header/**/*.*'},
        {pattern: 'templates/components/tabbed/**/*.*'},
        {pattern: 'templates/components/card/**/*.*'},
        {pattern: 'templates/financial-assistance/**/*.*'},
        {pattern: 'templates/search/**/*.*'},
        {pattern: 'templates/discovery/**/*.*'},
        {pattern: 'common/templates/**/*.*'},
        {pattern: 'teams/templates/**/*.*'},
        {pattern: 'support/templates/**/*.*'},
        {pattern: 'templates/bookmarks/**/*.*'},
        {pattern: 'templates/learner_dashboard/**/*.*'},
        {pattern: 'templates/ccx/**/*.*'},
        {pattern: 'templates/commerce/receipt.underscore'},
        {pattern: 'templates/api_admin/**/*.*', included: false}
    ],

    runFiles: [
        {pattern: 'js/spec/main.js', included: true}
    ]
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files
    });
};
