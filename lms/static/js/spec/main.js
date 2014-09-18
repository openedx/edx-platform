(function(requirejs, define) {

    // TODO: how can we share the vast majority of this config that is in common with CMS?
    requirejs.config({
        paths: {
            'gettext': 'xmodule_js/common_static/js/test/i18n',
            'mustache': 'xmodule_js/common_static/js/vendor/mustache',
            'codemirror': 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror',
            'jquery': 'xmodule_js/common_static/js/vendor/jquery.min',
            'jquery.ui': 'xmodule_js/common_static/js/vendor/jquery-ui.min',
            'jquery.form': 'xmodule_js/common_static/js/vendor/jquery.form',
            'jquery.markitup': 'xmodule_js/common_static/js/vendor/markitup/jquery.markitup',
            'jquery.leanModal': 'xmodule_js/common_static/js/vendor/jquery.leanModal.min',
            'jquery.ajaxQueue': 'xmodule_js/common_static/js/vendor/jquery.ajaxQueue',
            'jquery.smoothScroll': 'xmodule_js/common_static/js/vendor/jquery.smooth-scroll.min',
            'jquery.scrollTo': 'xmodule_js/common_static/js/vendor/jquery.scrollTo-1.4.2-min',
            'jquery.timepicker': 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker',
            'jquery.cookie': 'xmodule_js/common_static/js/vendor/jquery.cookie',
            'jquery.qtip': 'xmodule_js/common_static/js/vendor/jquery.qtip.min',
            'jquery.fileupload': 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload',
            'jquery.iframe-transport': 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport',
            'jquery.inputnumber': 'xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill',
            'jquery.immediateDescendents': 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents',
            'jquery.simulate': 'xmodule_js/common_static/js/vendor/jquery.simulate',
            'datepair': 'xmodule_js/common_static/js/vendor/timepicker/datepair',
            'date': 'xmodule_js/common_static/js/vendor/date',
            'underscore': 'xmodule_js/common_static/js/vendor/underscore-min',
            'underscore.string': 'xmodule_js/common_static/js/vendor/underscore.string.min',
            'backbone': 'xmodule_js/common_static/js/vendor/backbone-min',
            'backbone.associations': 'xmodule_js/common_static/js/vendor/backbone-associations-min',
            'backbone.paginator': 'xmodule_js/common_static/js/vendor/backbone.paginator.min',
            'tinymce': 'xmodule_js/common_static/js/vendor/tinymce/js/tinymce/tinymce.full.min',
            'jquery.tinymce': 'xmodule_js/common_static/js/vendor/tinymce/js/tinymce/jquery.tinymce',
            'xmodule': 'xmodule_js/src/xmodule',
            'utility': 'xmodule_js/common_static/js/src/utility',
            'accessibility': 'xmodule_js/common_static/js/src/accessibility_tools',
            'sinon': 'xmodule_js/common_static/js/vendor/sinon-1.7.1',
            'squire': 'xmodule_js/common_static/js/vendor/Squire',
            'jasmine-jquery': 'xmodule_js/common_static/js/vendor/jasmine-jquery',
            'jasmine-imagediff': 'xmodule_js/common_static/js/vendor/jasmine-imagediff',
            'jasmine-stealth': 'xmodule_js/common_static/js/vendor/jasmine-stealth',
            'jasmine.async': 'xmodule_js/common_static/js/vendor/jasmine.async',
            'draggabilly': 'xmodule_js/common_static/js/vendor/draggabilly.pkgd',
            'domReady': 'xmodule_js/common_static/js/vendor/domReady',
            'URI': 'xmodule_js/common_static/js/vendor/URI.min',
            'mathjax': '//edx-static.s3.amazonaws.com/mathjax-MathJax-727332c/MathJax.js?config=TeX-MML-AM_HTMLorMML-full&delayStartupUntil=configured',
            'youtube': '//www.youtube.com/player_api?noext',
            'tender': '//edxedge.tenderapp.com/tender_widget',
            'coffee/src/ajax_prefix': 'xmodule_js/common_static/coffee/src/ajax_prefix',
            'xblock/core': 'xmodule_js/common_static/coffee/src/xblock/core',
            'xblock/runtime.v1': 'xmodule_js/common_static/coffee/src/xblock/runtime.v1',
            'xblock/lms.runtime.v1': 'coffee/src/xblock/lms.runtime.v1',

            // Manually specify LMS files that are not converted to RequireJS
            'js/verify_student/photocapture': 'js/verify_student/photocapture',
            'js/staff_debug_actions': 'js/staff_debug_actions',
            'coffee/src/modules/tab': 'coffee/src/modules/tab',
            'coffee/src/calculator': 'coffee/src/calculator',
            'coffee/src/courseware': 'coffee/src/courseware',
            'coffee/src/feedback_form': 'coffee/src/feedback_form',
            'coffee/src/histogram': 'coffee/src/histogram',
            'coffee/src/logger': 'xmodule_js/common_static/coffee/src/logger',
            'coffee/src/navigation': 'coffee/src/navigation',
            'coffee/src/staff_grading/staff_grading': 'coffee/src/staff_grading/staff_grading',

            // Backbone classes loaded explicitly until they are converted to use RequireJS
            'js/models/cohort': 'js/models/cohort',
            'js/collections/cohort': 'js/collections/cohort',
            'js/views/cohort_editor': 'js/views/cohort_editor',
            'js/views/cohorts': 'js/views/cohorts'
        },
        shim: {
            'gettext': {
                exports: 'gettext'
            },
            'date': {
                exports: 'Date'
            },
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
                deps: ['jquery.iframe-transport'],
                exports: 'jQuery.fn.fileupload'
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
                exports: 'Backbone.Paginator'
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
                    MathJax.Hub.Config({
                        tex2jax: {
                            inlineMath: [['\\(', '\\)'], ['[mathjaxinline]', '[/mathjaxinline]']],
                            displayMath: [['\\[', '\\]'], ['[mathjax]', '[/mathjax]']]
                        }
                    });
                    return MathJax.Hub.Configured();
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
            'jasmine-jquery': {
                deps: ['jasmine']
            },
            'jasmine-imagediff': {
                deps: ['jasmine']
            },
            'jasmine-stealth': {
                deps: ['jasmine']
            },
            'jasmine.async': {
                deps: ['jasmine'],
                exports: 'AsyncSpec'
            },
            'xblock/core': {
                exports: 'XBlock',
                deps: ['jquery', 'jquery.immediateDescendents']
            },
            'xblock/runtime.v1': {
                exports: 'XBlock.Runtime.v1',
                deps: ['xblock/core']
            },
            'xblock/lms.runtime.v1': {
                exports: 'LmsRuntime.v1',
                deps: ['xblock/runtime.v1']
            },

            // LMS class loaded explicitly until they are converted to use RequireJS
            'js/verify_student/photocapture': {
                exports: 'js/verify_student/photocapture'
            },
            'js/staff_debug_actions': {
                exports: 'js/staff_debug_actions',
                deps: ['gettext']
            },
            'coffee/src/calculator': {
                exports: 'Calculator'
            },
            'coffee/src/courseware': {
                exports: 'Courseware',
                deps: ['xblock/lms.runtime.v1']
            },
            'coffee/src/feedback_form': {
                exports: 'FeedbackForm'
            },
            'coffee/src/histogram': {
                exports: 'Histogram'
            },
            'coffee/src/logger': {
                exports: 'Logger'
            },
            'coffee/src/navigation': {
                exports: 'Navigation'
            },
            'coffee/src/modules/tab': {
                exports: 'Tab'
            },
            'coffee/src/staff_grading/staff_grading': {
                exports: 'StaffGrading',
                deps: ['coffee/src/ajax_prefix', 'coffee/src/logger']
            },

            // Backbone classes loaded explicitly until they are converted to use RequireJS
            'js/models/cohort': {
                exports: 'CohortModel',
                deps: ['backbone']
            },
            'js/collections/cohort': {
                exports: 'CohortCollection',
                deps: ['backbone', 'js/models/cohort']
            },
            'js/views/cohort_editor': {
                exports: 'CohortsEditor',
                deps: ['backbone', 'js/collections/cohort']
            },
            'js/views/cohorts': {
                exports: 'CohortsView',
                deps: ['backbone', 'js/views/cohort_editor']
            }
        }
    });

    // TODO: why does this need 'lms/include' at the front but the CMS version doesn't?
    define([
        'lms/include/coffee/spec/helper.js',
        'lms/include/coffee/spec/modules/tab_spec.js',
        'lms/include/coffee/spec/calculator_spec.js',
        'lms/include/coffee/spec/courseware_spec.js',
        'lms/include/coffee/spec/feedback_form_spec.js',
        'lms/include/coffee/spec/histogram_spec.js',
        'lms/include/coffee/spec/navigation_spec.js',
        'lms/include/coffee/spec/requirejs_spec.js',
        'lms/include/coffee/spec/staff_grading_spec.js',
        'lms/include/js/spec/views/cohorts_spec.js',
        'lms/include/js/spec/photocapture_spec.js',
        'lms/include/js/spec/staff_debug_actions_spec.js'
    ]);

}).call(this, requirejs, define);
