/* globals requirejs, requireSerial */
/* eslint-disable quote-props */

(function(requirejs, requireSerial) {
    'use strict';

    if (window) {
        define('add-a11y-deps',
            [
                'underscore',
                'underscore.string',
                'common/static/edx-ui-toolkit/js/utils/html-utils',
                'common/static/edx-ui-toolkit/js/utils/string-utils'
            ], function(_, str, HtmlUtils, StringUtils) {
                window._ = _;
                window._.str = str;
                window.edx = window.edx || {};
                window.edx.HtmlUtils = HtmlUtils;
                window.edx.StringUtils = StringUtils;
            });
    }

    var i, specHelpers, testFiles;

    requirejs.config({
        baseUrl: '/base/',
        paths: {
            'gettext': 'common/static/js/test/i18n',
            'codemirror': 'common/static/js/vendor/CodeMirror/codemirror',
            'jquery': 'cms/static/js/vendor/jquery',
            'jquery-migrate': 'cms/static/js/vendor/jquery-migrate',
            'jquery.ui': 'cms/static/js/vendor/jquery-ui.min',
            'jquery.form': 'cms/static/js/vendor/jquery.form',
            'jquery.markitup': 'cms/static/js/vendor/markitup/jquery.markitup',
            'jquery.leanModal': 'cms/static/js/vendor/jquery.leanModal',
            'jquery.ajaxQueue': 'cms/static/js/vendor/jquery.ajaxQueue',
            'jquery.smoothScroll': 'cms/static/js/vendor/jquery.smooth-scroll.min',
            'jquery.scrollTo': 'cms/static/common/js/vendor/jquery.scrollTo',
            'jquery.timepicker': 'cms/static/js/vendor/timepicker/jquery.timepicker',
            'jquery.cookie': 'cms/static/js/vendor/jquery.cookie',
            'jquery.qtip': 'cms/static/js/vendor/jquery.qtip.min',
            'jquery.fileupload': 'cms/static/js/vendor/jQuery-File-Upload/js/jquery.fileupload',
            'jquery.fileupload-process': 'cms/static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-process',   // eslint-disable-line max-len
            'jquery.fileupload-validate': 'cms/static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-validate',   // eslint-disable-line max-len
            'jquery.iframe-transport': 'cms/static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport',   // eslint-disable-line max-len
            'jquery.inputnumber': 'cms/static/js/vendor/html5-input-polyfills/number-polyfill',
            'jquery.immediateDescendents': 'cms/static/coffee/src/jquery.immediateDescendents',
            'jquery.simulate': 'cms/static/js/vendor/jquery.simulate',
            'datepair': 'cms/static/js/vendor/timepicker/datepair',
            'date': 'cms/static/js/vendor/date',
            'moment': 'cms/static/common/js/vendor/moment-with-locales',
            'text': 'cms/static/js/vendor/requirejs/text',
            'underscore': 'cms/static/common/js/vendor/underscore',
            'underscore.string': 'cms/static/common/js/vendor/underscore.string',
            'backbone': 'cms/static/common/js/vendor/backbone',
            'backbone.associations': 'cms/static/js/vendor/backbone-associations-min',
            'backbone.paginator': 'cms/static/common/js/vendor/backbone.paginator',
            'backbone-relational': 'cms/static/js/vendor/backbone-relational.min',
            'tinymce': 'cms/static/js/vendor/tinymce/js/tinymce/tinymce.full.min',
            'jquery.tinymce': 'cms/static/js/vendor/tinymce/js/tinymce/jquery.tinymce',
            'xmodule': 'common/lib/xmodule/xmodule/js/src/xmodule',
            'xblock/cms.runtime.v1': 'cms/static/cms/js/xblock/cms.runtime.v1',
            'xblock': 'cms/static/common/js/xblock',
            'utility': 'cms/static/js/src/utility',
            'accessibility': 'cms/static/js/src/accessibility_tools',
            'sinon': 'cms/static/common/js/vendor/sinon',
            'squire': 'cms/static/common/js/vendor/Squire',
            'jasmine-imagediff': 'cms/static/js/vendor/jasmine-imagediff',
            'draggabilly': 'cms/static/js/vendor/draggabilly',
            'domReady': 'cms/static/js/vendor/domReady',
            'URI': 'cms/static/js/vendor/URI.min',
            'mock-ajax': 'cms/static/js/vendor/mock-ajax',
            'mathjax': '//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_SVG&delayStartupUntil=configured',   // eslint-disable-line max-len
            'youtube': '//www.youtube.com/player_api?noext',
            'coffee/src/ajax_prefix': 'cms/static/coffee/src/ajax_prefix',
            'js/spec/test_utils': 'cms/static/js/spec/test_utils'
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
            'accessibility': {
                exports: 'accessibility',
                deps: ['add-a11y-deps']
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
            'cms/static/common/js/spec_helpers/jasmine-extensions': {
                deps: ['jquery']
            },
            'cms/static/common/js/spec_helpers/jasmine-stealth': {
                deps: ['underscore', 'underscore.string']
            },
            'cms/static/common/js/spec_helpers/jasmine-waituntil': {
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
            'cms/static/cms/js/main': {
                deps: ['coffee/src/ajax_prefix']
            },
            'coffee/src/ajax_prefix': {
                deps: ['jquery']
            }
        }
    });

    jasmine.getFixtures().fixturesPath += 'coffee/fixtures';

    testFiles = [
        'cms/static/cms/js/spec/main_spec',
        'cms/static/cms/js/spec/xblock/cms.runtime.v1_spec',
        'cms/static/coffee/spec/models/course_spec',
        'cms/static/coffee/spec/models/metadata_spec',
        'cms/static/coffee/spec/models/section_spec',
        'cms/static/coffee/spec/models/settings_course_grader_spec',
        'cms/static/coffee/spec/models/settings_grading_spec',
        'cms/static/coffee/spec/models/textbook_spec',
        'cms/static/coffee/spec/models/upload_spec',
        'cms/static/coffee/spec/views/course_info_spec',
        'cms/static/coffee/spec/views/metadata_edit_spec',
        'cms/static/coffee/spec/views/textbook_spec',
        'cms/static/coffee/spec/views/upload_spec',
        'cms/static/js/spec/video/transcripts/utils_spec',
        'cms/static/js/spec/video/transcripts/editor_spec',
        'cms/static/js/spec/video/transcripts/videolist_spec',
        'cms/static/js/spec/video/transcripts/message_manager_spec',
        'cms/static/js/spec/video/transcripts/file_uploader_spec',
        'cms/static/js/spec/models/component_template_spec',
        'cms/static/js/spec/models/explicit_url_spec',
        'cms/static/js/spec/models/xblock_info_spec',
        'cms/static/js/spec/models/xblock_validation_spec',
        'cms/static/js/spec/models/license_spec',
        'cms/static/js/spec/utils/drag_and_drop_spec',
        'cms/static/js/spec/utils/handle_iframe_binding_spec',
        'cms/static/js/spec/utils/module_spec',
        'cms/static/js/spec/views/active_video_upload_list_spec',
        'cms/static/js/spec/views/previous_video_upload_spec',
        'cms/static/js/spec/views/video_thumbnail_spec',
        'cms/static/js/spec/views/course_video_settings_spec',
        'cms/static/js/spec/views/previous_video_upload_list_spec',
        'cms/static/js/spec/views/assets_spec',
        'cms/static/js/spec/views/baseview_spec',
        'cms/static/js/spec/views/container_spec',
        'cms/static/js/spec/views/module_edit_spec',
        'cms/static/js/spec/views/paged_container_spec',
        'cms/static/js/spec/views/group_configuration_spec',
        'cms/static/js/spec/views/unit_outline_spec',
        'cms/static/js/spec/views/xblock_spec',
        'cms/static/js/spec/views/xblock_editor_spec',
        'cms/static/js/spec/views/xblock_string_field_editor_spec',
        'cms/static/js/spec/views/xblock_validation_spec',
        'cms/static/js/spec/views/license_spec',
        'cms/static/js/spec/views/paging_spec',
        'cms/static/js/spec/views/login_studio_spec',
        'cms/static/js/spec/views/pages/container_spec',
        'cms/static/js/spec/views/pages/container_subviews_spec',
        'cms/static/js/spec/views/pages/group_configurations_spec',
        'cms/static/js/spec/views/pages/course_outline_spec',
        'cms/static/js/spec/views/pages/course_rerun_spec',
        'cms/static/js/spec/views/pages/index_spec',
        'cms/static/js/spec/views/pages/library_users_spec',
        'cms/static/js/spec/views/modals/base_modal_spec',
        'cms/static/js/spec/views/modals/edit_xblock_spec',
        'cms/static/js/spec/views/modals/move_xblock_modal_spec',
        'cms/static/js/spec/views/modals/validation_error_modal_spec',
        'cms/static/js/spec/views/move_xblock_spec',
        'cms/static/js/spec/views/settings/main_spec',
        'cms/static/js/spec/factories/xblock_validation_spec',
        'cms/static/js/certificates/spec/models/certificate_spec',
        'cms/static/js/certificates/spec/views/certificate_details_spec',
        'cms/static/js/certificates/spec/views/certificate_editor_spec',
        'cms/static/js/certificates/spec/views/certificates_list_spec',
        'cms/static/js/certificates/spec/views/certificate_preview_spec'
    ];

    i = 0;

    while (i < testFiles.length) {
        testFiles[i] = '/base/' + testFiles[i] + '.js';
        i++;
    }

    specHelpers = [
        'cms/static/common/js/spec_helpers/jasmine-extensions',
        'cms/static/common/js/spec_helpers/jasmine-stealth',
        'cms/static/common/js/spec_helpers/jasmine-waituntil'
    ];

    requireSerial(specHelpers.concat(testFiles), function() {
        return window.__karma__.start();  // eslint-disable-line no-underscore-dangle
    });
}).call(this, requirejs, requireSerial);
