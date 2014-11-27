(function(requirejs, define) {

    // TODO: how can we share the vast majority of this config that is in common with CMS?
    requirejs.config({
        paths: {
            'gettext': 'xmodule_js/common_static/js/test/i18n',
            'mustache': 'xmodule_js/common_static/js/vendor/mustache',
            'codemirror': 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror',
            'jquery': 'xmodule_js/common_static/js/vendor/jquery.min',
            'jquery.ui': 'xmodule_js/common_static/js/vendor/jquery-ui.min',
            'jquery.flot': 'xmodule_js/common_static/js/vendor/flot/jquery.flot.min',
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
            'jquery.url': 'xmodule_js/common_static/js/vendor/url.min',
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
            'mathjax': '//cdn.mathjax.org/mathjax/2.2-latest/MathJax.js?config=TeX-MML-AM_HTMLorMML-full&delayStartupUntil=configured',
            'youtube': '//www.youtube.com/player_api?noext',
            'tender': '//edxedge.tenderapp.com/tender_widget',
            'coffee/src/ajax_prefix': 'xmodule_js/common_static/coffee/src/ajax_prefix',
            'xmodule_js/common_static/js/test/add_ajax_prefix': 'xmodule_js/common_static/js/test/add_ajax_prefix',
            'xblock/core': 'xmodule_js/common_static/coffee/src/xblock/core',
            'xblock/runtime.v1': 'xmodule_js/common_static/coffee/src/xblock/runtime.v1',
            'xblock/lms.runtime.v1': 'coffee/src/xblock/lms.runtime.v1',
            'capa/display': 'xmodule_js/src/capa/display',
            'string_utils': 'xmodule_js/common_static/js/src/string_utils',

            // Manually specify LMS files that are not converted to RequireJS
            'js/verify_student/photocapture': 'js/verify_student/photocapture',
            'js/staff_debug_actions': 'js/staff_debug_actions',

            // Backbone classes loaded explicitly until they are converted to use RequireJS
            'js/models/file_uploader': 'js/models/file_uploader',
            'js/views/file_uploader': 'js/views/file_uploader',
            'js/models/cohort': 'js/models/cohort',
            'js/collections/cohort': 'js/collections/cohort',
            'js/views/cohort_editor': 'js/views/cohort_editor',
            'js/views/cohorts': 'js/views/cohorts',
            'js/views/notification': 'js/views/notification',
            'js/models/notification': 'js/models/notification',
            'js/student_account/account': 'js/student_account/account',
            'js/student_account/views/FormView': 'js/student_account/views/FormView',
            'js/student_account/models/LoginModel': 'js/student_account/models/LoginModel',
            'js/student_account/views/LoginView': 'js/student_account/views/LoginView',
            'js/student_account/models/PasswordResetModel': 'js/student_account/models/PasswordResetModel',
            'js/student_account/views/PasswordResetView': 'js/student_account/views/PasswordResetView',
            'js/student_account/models/RegisterModel': 'js/student_account/models/RegisterModel',
            'js/student_account/views/RegisterView': 'js/student_account/views/RegisterView',
            'js/student_account/views/AccessView': 'js/student_account/views/AccessView',
            'js/student_profile/profile': 'js/student_profile/profile'
        },
        shim: {
            'gettext': {
                exports: 'gettext'
            },
            'string_utils': {
                deps: ['underscore'],
                exports: 'interpolate_text'
            },
            'date': {
                exports: 'Date'
            },
            'jquery.ui': {
                deps: ['jquery'],
                exports: 'jQuery.ui'
            },
            'jquery.flot': {
                deps: ['jquery'],
                exports: 'jQuery.flot'
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
            'jquery.url': {
                deps: ['jquery'],
                exports: 'jQuery.fn.url'
            },
            'datepair': {
                deps: ['jquery.ui', 'jquery.timepicker']
            },
            'underscore': {
                deps: ['underscore.string'],
                exports: '_',
                init: function(UnderscoreString) {
                    /* Mix non-conflicting functions from underscore.string
                     * (all but include, contains, and reverse) into the
                     * Underscore namespace. This allows the login, register,
                     * and password reset templates to render independent of the
                     * access view.
                     */
                    _.mixin(UnderscoreString.exports());

                    /* Since the access view is not using RequireJS, we also
                     * expose underscore.string at _.str, so that the access
                     * view can perform the mixin on its own.
                     */
                    _.str = UnderscoreString;
                }
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
            'xmodule_js/common_static/js/test/add_ajax_prefix': {
                exports: 'AjaxPrefix',
                deps: ['coffee/src/ajax_prefix']
            },

            // LMS class loaded explicitly until they are converted to use RequireJS
            'js/student_account/account': {
                exports: 'js/student_account/account',
                deps: ['jquery', 'underscore', 'backbone', 'gettext', 'jquery.cookie']
            },
            'js/student_profile/profile': {
                exports: 'js/student_profile/profile',
                deps: ['jquery', 'underscore', 'backbone', 'gettext', 'jquery.cookie']
            },
            'js/verify_student/photocapture': {
                exports: 'js/verify_student/photocapture'
            },
            'js/staff_debug_actions': {
                exports: 'js/staff_debug_actions',
                deps: ['gettext']
            },
            'js/dashboard/donation.js': {
                exports: 'js/dashboard/donation',
                deps: ['jquery', 'underscore', 'gettext']
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
                deps: ['backbone', 'jquery', 'underscore', 'js/views/notification', 'js/models/notification',
                    'string_utils'
                ]
            },
            'js/views/cohorts': {
                exports: 'CohortsView',
                deps: ['jquery', 'underscore', 'backbone', 'gettext', 'string_utils', 'js/views/cohort_editor',
                    'js/views/notification', 'js/models/notification', 'js/views/file_uploader',
                    'js/models/file_uploader'
                ]
            },
            'js/models/notification': {
                exports: 'NotificationModel',
                deps: ['backbone']
            },
            'js/views/notification': {
                exports: 'NotificationView',
                deps: ['backbone', 'jquery', 'underscore']
            },
            'js/models/file_uploader': {
                exports: 'FileUploaderModel',
                deps: ['backbone']
            },
            'js/views/file_uploader': {
                exports: 'FileUploaderView',
                deps: ['backbone', 'jquery', 'underscore', 'gettext', 'string_utils', 'js/views/notification',
                    'js/models/notification', 'jquery.fileupload'
                ]
            },
            'js/student_account/enrollment': {
                exports: 'edx.student.account.EnrollmentInterface',
                deps: ['jquery', 'jquery.cookie']
            },
            'js/student_account/shoppingcart': {
                exports: 'edx.student.account.ShoppingCartInterface',
                deps: ['jquery', 'jquery.cookie', 'underscore']
            },
            // Student account registration/login
            // Loaded explicitly until these are converted to RequireJS
            'js/student_account/views/FormView': {
                exports: 'edx.student.account.FormView',
                deps: ['jquery', 'underscore', 'backbone', 'gettext']
            },
            'js/student_account/models/LoginModel': {
                exports: 'edx.student.account.LoginModel',
                deps: ['jquery', 'jquery.cookie', 'backbone']
            },
            'js/student_account/views/LoginView': {
                exports: 'edx.student.account.LoginView',
                deps: [
                    'jquery',
                    'jquery.url',
                    'underscore',
                    'gettext',
                    'js/student_account/models/LoginModel',
                    'js/student_account/views/FormView'
                ]
            },
            'js/student_account/models/PasswordResetModel': {
                exports: 'edx.student.account.PasswordResetModel',
                deps: ['jquery', 'jquery.cookie', 'backbone']
            },
            'js/student_account/views/PasswordResetView': {
                exports: 'edx.student.account.PasswordResetView',
                deps: [
                    'jquery',
                    'underscore',
                    'gettext',
                    'js/student_account/models/PasswordResetModel',
                    'js/student_account/views/FormView'
                ]
            },
            'js/student_account/models/RegisterModel': {
                exports: 'edx.student.account.RegisterModel',
                deps: ['jquery', 'jquery.cookie', 'backbone']
            },
            'js/student_account/views/RegisterView': {
                exports: 'edx.student.account.RegisterView',
                deps: [
                    'jquery',
                    'jquery.url',
                    'underscore',
                    'gettext',
                    'js/student_account/models/RegisterModel',
                    'js/student_account/views/FormView'
                ]
            },
            'js/student_account/views/AccessView': {
                exports: 'edx.student.account.AccessView',
                deps: [
                    'jquery',
                    'underscore',
                    'backbone',
                    'gettext',
                    'utility',
                    'js/student_account/views/LoginView',
                    'js/student_account/views/PasswordResetView',
                    'js/student_account/views/RegisterView',
                    'js/student_account/models/LoginModel',
                    'js/student_account/models/PasswordResetModel',
                    'js/student_account/models/RegisterModel',
                    'js/student_account/views/FormView',
                    'js/student_account/enrollment',
                    'js/student_account/shoppingcart',
                ]
            }
        }
    });

    // TODO: why do these need 'lms/include' at the front but the CMS equivalent logic doesn't?
    define([
        // Run the LMS tests
        'lms/include/js/spec/views/cohorts_spec.js',
        'lms/include/js/spec/photocapture_spec.js',
        'lms/include/js/spec/staff_debug_actions_spec.js',
        'lms/include/js/spec/views/notification_spec.js',
        'lms/include/js/spec/views/file_uploader_spec.js',
        'lms/include/js/spec/dashboard/donation.js',
        'lms/include/js/spec/student_account/account_spec.js',
        'lms/include/js/spec/student_account/access_spec.js',
        'lms/include/js/spec/student_account/login_spec.js',
        'lms/include/js/spec/student_account/register_spec.js',
        'lms/include/js/spec/student_account/password_reset_spec.js',
        'lms/include/js/spec/student_account/enrollment_spec.js',
        'lms/include/js/spec/student_account/shoppingcart_spec.js',
        'lms/include/js/spec/student_profile/profile_spec.js'
    ]);

}).call(this, requirejs, define);
