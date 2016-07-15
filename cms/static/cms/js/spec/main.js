(function(requirejs, requireSerial) {
    'use strict';

    var i, specHelpers, testFiles;

    requirejs.config({
        baseUrl: '/base/',
        paths: {
            'gettext': 'xmodule_js/common_static/js/test/i18n',
            'mustache': 'xmodule_js/common_static/js/vendor/mustache',
            'codemirror': 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror',
            'jquery': 'xmodule_js/common_static/common/js/vendor/jquery',
            'jquery-migrate': 'xmodule_js/common_static/common/js/vendor/jquery-migrate',
            'jquery.ui': 'xmodule_js/common_static/js/vendor/jquery-ui.min',
            'jquery.form': 'xmodule_js/common_static/js/vendor/jquery.form',
            'jquery.markitup': 'xmodule_js/common_static/js/vendor/markitup/jquery.markitup',
            'jquery.leanModal': 'xmodule_js/common_static/js/vendor/jquery.leanModal',
            'jquery.ajaxQueue': 'xmodule_js/common_static/js/vendor/jquery.ajaxQueue',
            'jquery.smoothScroll': 'xmodule_js/common_static/js/vendor/jquery.smooth-scroll.min',
            'jquery.scrollTo': 'common/js/vendor/jquery.scrollTo',
            'jquery.timepicker': 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker',
            'jquery.cookie': 'xmodule_js/common_static/js/vendor/jquery.cookie',
            'jquery.qtip': 'xmodule_js/common_static/js/vendor/jquery.qtip.min',
            'jquery.fileupload': 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload',
            'jquery.fileupload-process': 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-process',  // jshint ignore:line
            'jquery.fileupload-validate': 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-validate',  // jshint ignore:line
            'jquery.iframe-transport': 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport',  // jshint ignore:line
            'jquery.inputnumber': 'xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill',
            'jquery.immediateDescendents': 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents',
            'jquery.simulate': 'xmodule_js/common_static/js/vendor/jquery.simulate',
            'datepair': 'xmodule_js/common_static/js/vendor/timepicker/datepair',
            'date': 'xmodule_js/common_static/js/vendor/date',
            'moment': 'xmodule_js/common_static/js/vendor/moment.min',
            'moment-with-locales': 'xmodule_js/common_static/js/vendor/moment-with-locales.min',
            'text': 'xmodule_js/common_static/js/vendor/requirejs/text',
            'underscore': 'common/js/vendor/underscore',
            'underscore.string': 'common/js/vendor/underscore.string',
            'backbone': 'common/js/vendor/backbone',
            'backbone.associations': 'xmodule_js/common_static/js/vendor/backbone-associations-min',
            'backbone.paginator': 'common/js/vendor/backbone.paginator',
            'backbone-relational': 'xmodule_js/common_static/js/vendor/backbone-relational.min',
            'tinymce': 'xmodule_js/common_static/js/vendor/tinymce/js/tinymce/tinymce.full.min',
            'jquery.tinymce': 'xmodule_js/common_static/js/vendor/tinymce/js/tinymce/jquery.tinymce',
            'xmodule': 'xmodule_js/src/xmodule',
            'xblock/cms.runtime.v1': 'cms/js/xblock/cms.runtime.v1',
            'xblock': 'common/js/xblock',
            'utility': 'xmodule_js/common_static/js/src/utility',
            'accessibility': 'xmodule_js/common_static/js/src/accessibility_tools',
            'sinon': 'xmodule_js/common_static/js/vendor/sinon-1.17.0',
            'squire': 'xmodule_js/common_static/js/vendor/Squire',
            'jasmine-imagediff': 'xmodule_js/common_static/js/vendor/jasmine-imagediff',
            'draggabilly': 'xmodule_js/common_static/js/vendor/draggabilly',
            'domReady': 'xmodule_js/common_static/js/vendor/domReady',
            'URI': 'xmodule_js/common_static/js/vendor/URI.min',
            'mock-ajax': 'xmodule_js/common_static/js/vendor/mock-ajax',
            'mathjax': '//cdn.mathjax.org/mathjax/2.6-latest/MathJax.js?config=TeX-MML-AM_SVG&delayStartupUntil=configured',  // jshint ignore:line
            'youtube': '//www.youtube.com/player_api?noext',
            'coffee/src/ajax_prefix': 'xmodule_js/common_static/coffee/src/ajax_prefix',
            'js/spec/test_utils': 'js/spec/test_utils'
        },
        shim: {
            'gettext': {
                exports: 'gettext'
            },
            'date': {
                exports: 'Date'
            },
            'jquery-migrate': ['jquery'],
            'jquery.ui': {
                deps: ['jquery'],
                exports: 'jQuery.ui'
            },
            'jquery.form': {
                deps: ['jquery'],
                exports: 'jQuery.fn.ajaxForm'
            },
            'jquery.markitup': {
                deps: ['jquery'],
                exports: 'jQuery.fn.markitup'
            },
            'jquery.leanModal': {
                deps: ['jquery'],
                exports: 'jQuery.fn.leanModal'
            },
            'jquery.smoothScroll': {
                deps: ['jquery'],
                exports: 'jQuery.fn.smoothScroll'
            },
            'jquery.ajaxQueue': {
                deps: ['jquery'],
                exports: 'jQuery.fn.ajaxQueue'
            },
            'jquery.scrollTo': {
                deps: ['jquery'],
                exports: 'jQuery.fn.scrollTo'
            },
            'jquery.cookie': {
                deps: ['jquery'],
                exports: 'jQuery.fn.cookie'
            },
            'jquery.qtip': {
                deps: ['jquery'],
                exports: 'jQuery.fn.qtip'
            },
            'jquery.fileupload': {
                deps: ['jquery.ui', 'jquery.iframe-transport'],
                exports: 'jQuery.fn.fileupload'
            },
            'jquery.fileupload-process': {
                deps: ['jquery.fileupload']
            },
            'jquery.fileupload-validate': {
                deps: ['jquery.fileupload']
            },
            'jquery.inputnumber': {
                deps: ['jquery'],
                exports: 'jQuery.fn.inputNumber'
            },
            'jquery.simulate': {
                deps: ['jquery'],
                exports: 'jQuery.fn.simulate'
            },
            'jquery.tinymce': {
                deps: ['jquery', 'tinymce'],
                exports: 'jQuery.fn.tinymce'
            },
            'datepair': {
                deps: ['jquery.ui', 'jquery.timepicker']
            },
            'underscore': {
                exports: '_'
            },
            'backbone': {
                deps: ['underscore', 'jquery'],
                exports: 'Backbone'
            },
            'backbone.associations': {
                deps: ['backbone'],
                exports: 'Backbone.Associations'
            },
            'backbone.paginator': {
                deps: ['backbone'],
                exports: 'Backbone.PageableCollection'
            },
            'backbone-relational': {
                deps: ['backbone']
            },
            'youtube': {
                exports: 'YT'
            },
            'codemirror': {
                exports: 'CodeMirror'
            },
            'tinymce': {
                exports: 'tinymce'
            },
            'mathjax': {
                exports: 'MathJax',
                init: function() {
                    window.MathJax.Hub.Config({
                        tex2jax: {
                            inlineMath: [['\\(', '\\)'], ['[mathjaxinline]', '[/mathjaxinline]']],
                            displayMath: [['\\[', '\\]'], ['[mathjax]', '[/mathjax]']]
                        }
                    });
                    return window.MathJax.Hub.Configured();
                }
            },
            'URI': {
                exports: 'URI'
            },
            'xmodule': {
                exports: 'XModule'
            },
            'sinon': {
                exports: 'sinon'
            },
            'jasmine-imagediff': {},
            'common/js/spec_helpers/jasmine-extensions': {
                deps: ['jquery']
            },
            'common/js/spec_helpers/jasmine-stealth': {
                deps: ['underscore', 'underscore.string']
            },
            'common/js/spec_helpers/jasmine-waituntil': {
                deps: ['jquery']
            },
            'xblock/core': {
                exports: 'XBlock',
                deps: ['jquery', 'jquery.immediateDescendents']
            },
            'xblock/runtime.v1': {
                exports: 'XBlock',
                deps: ['xblock/core']
            },
            'mock-ajax': {
                deps: ['jquery']
            },
            'js/main': {
                deps: ['coffee/src/ajax_prefix']
            },
            'coffee/src/ajax_prefix': {
                deps: ['jquery']
            }
        }
    });

    jasmine.getFixtures().fixturesPath += 'coffee/fixtures';

    testFiles = [
        'cms/js/spec/xblock/cms.runtime.v1_spec',
        'coffee/spec/models/course_spec',
        'coffee/spec/models/metadata_spec',
        'coffee/spec/models/section_spec',
        'coffee/spec/models/settings_course_grader_spec',
        'coffee/spec/models/settings_grading_spec',
        'coffee/spec/models/textbook_spec',
        'coffee/spec/models/upload_spec',
        'js/spec/main_spec',
        'js/spec/video/transcripts/utils_spec',
        'js/spec/video/transcripts/editor_spec',
        'js/spec/video/transcripts/videolist_spec',
        'js/spec/video/transcripts/message_manager_spec',
        'js/spec/video/transcripts/file_uploader_spec',
        'js/spec/models/component_template_spec',
        'js/spec/models/explicit_url_spec',
        'js/spec/models/xblock_info_spec',
        'js/spec/models/xblock_validation_spec',
        'js/spec/models/license_spec',
        'js/spec/utils/drag_and_drop_spec',
        'js/spec/utils/handle_iframe_binding_spec',
        'js/spec/utils/module_spec',
        'js/spec/views/active_video_upload_list_spec',
        'js/spec/views/previous_video_upload_spec',
        'js/spec/views/previous_video_upload_list_spec',
        'js/spec/views/assets_spec',
        'js/spec/views/baseview_spec',
        'js/spec/views/container_spec',
        'js/spec/views/course_info_spec',
        'js/spec/views/metadata_edit_spec',
        'js/spec/views/module_edit_spec',
        'js/spec/views/paged_container_spec',
        'js/spec/views/group_configuration_spec',
        'js/spec/views/textbook_spec',
        'js/spec/views/unit_outline_spec',
        'js/spec/views/upload_spec',
        'js/spec/views/xblock_spec',
        'js/spec/views/xblock_editor_spec',
        'js/spec/views/xblock_string_field_editor_spec',
        'js/spec/views/xblock_validation_spec',
        'js/spec/views/license_spec',
        'js/spec/views/paging_spec',
        'js/spec/views/login_studio_spec',
        'js/spec/views/pages/container_spec',
        'js/spec/views/pages/container_subviews_spec',
        'js/spec/views/pages/group_configurations_spec',
        'js/spec/views/pages/course_outline_spec',
        'js/spec/views/pages/course_rerun_spec',
        'js/spec/views/pages/index_spec',
        'js/spec/views/pages/library_users_spec',
        'js/spec/views/modals/base_modal_spec',
        'js/spec/views/modals/edit_xblock_spec',
        'js/spec/views/modals/validation_error_modal_spec',
        'js/spec/views/settings/main_spec',
        'js/spec/factories/xblock_validation_spec',
        'js/certificates/spec/models/certificate_spec',
        'js/certificates/spec/views/certificate_details_spec',
        'js/certificates/spec/views/certificate_editor_spec',
        'js/certificates/spec/views/certificates_list_spec',
        'js/certificates/spec/views/certificate_preview_spec'
    ];

    i = 0;

    while (i < testFiles.length) {
        testFiles[i] = '/base/' + testFiles[i] + '.js';
        i++;
    }

    specHelpers = [
        'common/js/spec_helpers/jasmine-extensions',
        'common/js/spec_helpers/jasmine-stealth',
        'common/js/spec_helpers/jasmine-waituntil'
    ];

    requireSerial(specHelpers.concat(testFiles), function() {
        return window.__karma__.start();
    });

}).call(this, requirejs, requireSerial);  // jshint ignore:line
