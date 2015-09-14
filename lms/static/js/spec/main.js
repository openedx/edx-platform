(function(requirejs, define) {
    // TODO: how can we share the vast majority of this config that is in common with CMS?
    requirejs.config({
        paths: {
            'gettext': 'xmodule_js/common_static/js/test/i18n',
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
            'jquery.timeago': 'xmodule_js/common_static/js/vendor/jquery.timeago',
            'jquery.url': 'xmodule_js/common_static/js/vendor/url.min',
            'datepair': 'xmodule_js/common_static/js/vendor/timepicker/datepair',
            'date': 'xmodule_js/common_static/js/vendor/date',
            'moment': 'xmodule_js/common_static/js/vendor/moment.min',
            'moment-with-locales': 'xmodule_js/common_static/js/vendor/moment-with-locales.min',
            'text': 'xmodule_js/common_static/js/vendor/requirejs/text',
            'underscore': 'xmodule_js/common_static/js/vendor/underscore-min',
            'underscore.string': 'xmodule_js/common_static/js/vendor/underscore.string.min',
            'backbone': 'xmodule_js/common_static/js/vendor/backbone-min',
            'backbone.associations': 'xmodule_js/common_static/js/vendor/backbone-associations-min',
            'backbone.paginator': 'xmodule_js/common_static/js/vendor/backbone.paginator.min',
            'backbone-super': 'js/vendor/backbone-super',
            'URI': 'xmodule_js/common_static/js/vendor/URI.min',
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
            'mathjax': '//cdn.mathjax.org/mathjax/2.4-latest/MathJax.js?config=TeX-MML-AM_HTMLorMML-full&delayStartupUntil=configured',
            'youtube': '//www.youtube.com/player_api?noext',
            'coffee/src/ajax_prefix': 'xmodule_js/common_static/coffee/src/ajax_prefix',
            'coffee/src/instructor_dashboard/student_admin': 'coffee/src/instructor_dashboard/student_admin',
            'xmodule_js/common_static/js/test/add_ajax_prefix': 'xmodule_js/common_static/js/test/add_ajax_prefix',
            'xblock/core': 'xmodule_js/common_static/js/xblock/core',
            'xblock/runtime.v1': 'xmodule_js/common_static/coffee/src/xblock/runtime.v1',
            'xblock/lms.runtime.v1': 'coffee/src/xblock/lms.runtime.v1',
            'capa/display': 'xmodule_js/src/capa/display',
            'string_utils': 'xmodule_js/common_static/js/src/string_utils',
            'logger': 'xmodule_js/common_static/js/src/logger',
            'Markdown.Converter': 'js/Markdown.Converter',
            'Markdown.Editor': 'js/Markdown.Editor',
            'Markdown.Sanitizer': 'js/Markdown.Sanitizer',
            '_split': 'js/split',
            'mathjax_delay_renderer': 'coffee/src/mathjax_delay_renderer',
            'MathJaxProcessor': 'coffee/src/customwmd',

            // Manually specify LMS files that are not converted to RequireJS
            'history': 'js/vendor/history',
            'js/staff_debug_actions': 'js/staff_debug_actions',
            'js/vendor/jquery.qubit': 'js/vendor/jquery.qubit',

            // Backbone classes loaded explicitly until they are converted to use RequireJS
            'js/models/notification': 'js/models/notification',
            'js/views/file_uploader': 'js/views/file_uploader',
            'js/views/notification': 'js/views/notification',
            'js/student_account/account': 'js/student_account/account',
            'js/student_profile/views/learner_profile_fields': 'js/student_profile/views/learner_profile_fields',
            'js/student_profile/views/learner_profile_factory': 'js/student_profile/views/learner_profile_factory',
            'js/student_profile/views/learner_profile_view': 'js/student_profile/views/learner_profile_view',
            'js/ccx/schedule': 'js/ccx/schedule',

            // Discussion classes loaded explicitly until they are converted to use RequireJS
            'DiscussionModuleView': 'xmodule_js/common_static/coffee/src/discussion/discussion_module_view',

            // edxnotes
            'annotator_1.2.9': 'xmodule_js/common_static/js/vendor/edxnotes/annotator-full.min',

            // Common edx utils
            'js/utils/edx.utils.validate': 'xmodule_js/common_static/js/utils/edx.utils.validate'
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
            'jquery.timeago': {
                deps: ['jquery'],
                exports: 'jQuery.timeago'
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
            "backbone-super": {
                deps: ["backbone"]
            },
            'youtube': {
                exports: 'YT'
            },
            'Markdown.Converter': {
                deps: ['mathjax'],
                exports: 'Markdown.Converter'
            },
            'Markdown.Editor': {
                deps: ['Markdown.Converter'],
                exports: 'Markdown.Editor'
            },
            'Markdown.Sanitizer': {
                deps: ['Markdown.Converter'],
                exports: 'Markdown.Sanitizer'
            },
            '_split': {
                exports: '_split'
            },
            'MathJaxProcessor': {
                deps: [
                    'Markdown.Converter', 'Markdown.Sanitizer', 'Markdown.Editor', '_split', 'mathjax_delay_renderer'
                ],
                exports: 'MathJaxProcessor'
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
            'logger': {
                exports: 'Logger'
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
            'coffee/src/instructor_dashboard/student_admin': {
                exports: 'coffee/src/instructor_dashboard/student_admin',
                deps: ['jquery', 'underscore', 'coffee/src/instructor_dashboard/util', 'string_utils']
            },
            // LMS class loaded explicitly until they are converted to use RequireJS
            'js/student_account/account': {
                exports: 'js/student_account/account',
                deps: ['jquery', 'underscore', 'backbone', 'gettext', 'jquery.cookie']
            },
            'js/staff_debug_actions': {
                exports: 'js/staff_debug_actions',
                deps: ['gettext']
            },
            'js/dashboard/donation.js': {
                exports: 'js/dashboard/donation',
                deps: ['jquery', 'underscore', 'gettext']
            },
            'js/shoppingcart/shoppingcart.js': {
                exports: 'js/shoppingcart/shoppingcart',
                deps: ['jquery', 'underscore', 'gettext']
            },
            'js/ccx/schedule': {
                exports: 'js/ccx/schedule',
                deps: ['jquery', 'underscore', 'backbone', 'gettext']
            },

            // Backbone classes loaded explicitly until they are converted to use RequireJS
            'js/instructor_dashboard/ecommerce': {
                exports: 'edx.instructor_dashboard.ecommerce.ExpiryCouponView',
                deps: ['backbone', 'jquery', 'underscore']
            },
            'js/models/notification': {
                exports: 'NotificationModel',
                deps: ['backbone']
            },
            'js/views/notification': {
                exports: 'NotificationView',
                deps: ['backbone', 'jquery', 'underscore']
            },
            'js/views/file_uploader': {
                exports: 'FileUploaderView',
                deps: [
                    'backbone', 'jquery', 'underscore', 'gettext', 'string_utils', 'js/views/notification',
                    'js/models/notification', 'jquery.fileupload'
                ]
            },
            'js/verify_student/models/verification_model': {
                exports: 'edx.verify_student.VerificationModel',
                deps: [ 'jquery', 'underscore', 'backbone', 'jquery.cookie' ]
            },
            'js/verify_student/views/error_view': {
                exports: 'edx.verify_student.ErrorView',
                deps: [ 'jquery', 'underscore', 'backbone' ]
            },
            'js/verify_student/views/webcam_photo_view': {
                exports: 'edx.verify_student.WebcamPhotoView',
                deps: [
                    'jquery',
                    'underscore',
                    'backbone',
                    'gettext',
                    'js/verify_student/views/image_input_view'
                ]
            },
            'js/verify_student/views/image_input_view': {
                exports: 'edx.verify_student.ImageInputView',
                deps: [ 'jquery', 'underscore', 'backbone', 'gettext' ]
            },
            'js/verify_student/views/step_view': {
                exports: 'edx.verify_student.StepView',
                deps: [ 'jquery', 'underscore', 'underscore.string', 'backbone', 'gettext' ]
            },
            'js/verify_student/views/intro_step_view': {
                exports: 'edx.verify_student.IntroStepView',
                deps: [
                    'jquery',
                    'js/verify_student/views/step_view'
                ]
            },
            'js/verify_student/views/make_payment_step_view': {
                exports: 'edx.verify_student.MakePaymentStepView',
                deps: [
                    'jquery',
                    'underscore',
                    'gettext',
                    'jquery.cookie',
                    'jquery.url',
                    'string_utils',
                    'js/verify_student/views/step_view'
                ]
            },
            'js/verify_student/views/payment_confirmation_step_view': {
                exports: 'edx.verify_student.PaymentConfirmationStepView',
                deps: [
                    'jquery',
                    'underscore',
                    'gettext',
                    'js/verify_student/views/step_view'
                ]
            },
            'js/verify_student/views/face_photo_step_view': {
                exports: 'edx.verify_student.FacePhotoStepView',
                deps: [
                    'jquery',
                    'underscore',
                    'gettext',
                    'js/verify_student/views/step_view',
                    'js/verify_student/views/webcam_photo_view'
                ]
            },
            'js/verify_student/views/id_photo_step_view': {
                exports: 'edx.verify_student.IDPhotoStepView',
                deps: [
                    'jquery',
                    'underscore',
                    'gettext',
                    'js/verify_student/views/step_view',
                    'js/verify_student/views/webcam_photo_view'
                ]
            },
            'js/verify_student/views/review_photos_step_view': {
                exports: 'edx.verify_student.ReviewPhotosStepView',
                deps: [
                    'jquery',
                    'underscore',
                    'gettext',
                    'js/verify_student/views/step_view',
                    'js/verify_student/views/webcam_photo_view'
                ]
            },
            'js/verify_student/views/enrollment_confirmation_step_view': {
                exports: 'edx.verify_student.EnrollmentConfirmationStepView',
                deps: [
                    'jquery',
                    'js/verify_student/views/step_view'
                ]
            },
            'js/verify_student/views/reverify_success_step_view': {
                exports: 'edx.verify_student.ReverifySuccessStepView',
                deps: [
                    'jquery',
                    'js/verify_student/views/step_view'
                ]
            },
            'js/verify_student/views/pay_and_verify_view': {
                exports: 'edx.verify_student.PayAndVerifyView',
                deps: [
                    'jquery',
                    'underscore',
                    'backbone',
                    'gettext',
                    'js/verify_student/models/verification_model',
                    'js/verify_student/views/intro_step_view',
                    'js/verify_student/views/make_payment_step_view',
                    'js/verify_student/views/payment_confirmation_step_view',
                    'js/verify_student/views/face_photo_step_view',
                    'js/verify_student/views/id_photo_step_view',
                    'js/verify_student/views/review_photos_step_view',
                    'js/verify_student/views/enrollment_confirmation_step_view'
                ]
            },
            'js/verify_student/views/reverify_view': {
                exports: 'edx.verify_student.ReverifyView',
                deps: [
                    'jquery',
                    'underscore',
                    'backbone',
                    'gettext',
                    'js/verify_student/models/verification_model',
                    'js/verify_student/views/face_photo_step_view',
                    'js/verify_student/views/id_photo_step_view',
                    'js/verify_student/views/enrollment_confirmation_step_view',
                    'js/verify_student/views/reverify_success_step_view'
                ]
            },
            // Student Notes
            'annotator_1.2.9': {
                exports: 'Annotator',
                deps: ['jquery']
            },
            // Discussions
            'xmodule_js/common_static/coffee/src/discussion/utils': {
                deps: [
                    'jquery',
                    'jquery.timeago',
                    'underscore',
                    'backbone',
                    'gettext',
                    'MathJaxProcessor',
                    'URI'
                ],
                exports: 'DiscussionUtil',
                init: function() {
                    // Set global variables that the discussion code is expecting to be defined
                    window.Backbone = require('backbone');
                    window.URI = require('URI');
                }
            },
            'xmodule_js/common_static/coffee/src/discussion/content': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'Content'
            },
            'xmodule_js/common_static/coffee/src/discussion/discussion': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils',
                    'xmodule_js/common_static/coffee/src/discussion/content'
                ],
                exports: 'Discussion'
            },
            'xmodule_js/common_static/coffee/src/discussion/discussion_filter': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionFilter'
            },
            'xmodule_js/common_static/coffee/src/discussion/models/discussion_course_settings': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionCourseSettings'
            },
            'xmodule_js/common_static/coffee/src/discussion/models/discussion_user': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionUser'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_content_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionContentView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_edit_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionThreadEditView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_list_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionThreadListView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_profile_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionThreadProfileView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_show_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionThreadShowView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionThreadView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_topic_menu_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionTopicMenuView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/discussion_user_profile_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionUserProfileView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/new_post_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'NewPostView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/thread_response_edit_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'ThreadResponseEditView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/thread_response_show_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'ThreadResponseShowView'
            },
            'xmodule_js/common_static/coffee/src/discussion/views/thread_response_view': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'ThreadResponseView'
            },
            'DiscussionModuleView': {
                deps: [
                    'jquery',
                    'underscore',
                    'backbone',
                    'gettext',
                    'URI',
                    'xmodule_js/common_static/coffee/src/discussion/content',
                    'xmodule_js/common_static/coffee/src/discussion/discussion',
                    'xmodule_js/common_static/coffee/src/discussion/discussion_filter',
                    'xmodule_js/common_static/coffee/src/discussion/utils',
                    'xmodule_js/common_static/coffee/src/discussion/models/discussion_course_settings',
                    'xmodule_js/common_static/coffee/src/discussion/models/discussion_user',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_content_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_edit_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_list_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_profile_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_show_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_thread_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_topic_menu_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/discussion_user_profile_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/new_post_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/thread_response_edit_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/thread_response_show_view',
                    'xmodule_js/common_static/coffee/src/discussion/views/thread_response_view'
                ],
                exports: 'DiscussionModuleView'
            },
            'xmodule_js/common_static/coffee/spec/discussion/discussion_spec_helper': {
                deps: [
                    'xmodule_js/common_static/coffee/src/discussion/utils'
                ],
                exports: 'DiscussionSpecHelper'
            }

        }
    });

    // TODO: why do these need 'lms/include' at the front but the CMS equivalent logic doesn't?
    define([
        // Run the LMS tests
        'lms/include/js/spec/components/header/header_spec.js',
        'lms/include/js/spec/components/tabbed/tabbed_view_spec.js',
        'lms/include/js/spec/components/card/card_spec.js',
        'lms/include/js/spec/staff_debug_actions_spec.js',
        'lms/include/js/spec/views/notification_spec.js',
        'lms/include/js/spec/views/file_uploader_spec.js',
        'lms/include/js/spec/dashboard/donation.js',
        'lms/include/js/spec/groups/views/cohorts_spec.js',
        'lms/include/js/spec/shoppingcart/shoppingcart_spec.js',
        'lms/include/js/spec/instructor_dashboard/ecommerce_spec.js',
        'lms/include/js/spec/instructor_dashboard/student_admin_spec.js',
        'lms/include/js/spec/student_account/account_spec.js',
        'lms/include/js/spec/student_account/access_spec.js',
        'lms/include/js/spec/student_account/logistration_factory_spec.js',
        'lms/include/js/spec/student_account/finish_auth_spec.js',
        'lms/include/js/spec/student_account/hinted_login_spec.js',
        'lms/include/js/spec/student_account/login_spec.js',
        'lms/include/js/spec/student_account/institution_login_spec.js',
        'lms/include/js/spec/student_account/register_spec.js',
        'lms/include/js/spec/student_account/password_reset_spec.js',
        'lms/include/js/spec/student_account/enrollment_spec.js',
        'lms/include/js/spec/student_account/emailoptin_spec.js',
        'lms/include/js/spec/student_account/shoppingcart_spec.js',
        'lms/include/js/spec/student_account/account_settings_factory_spec.js',
        'lms/include/js/spec/student_account/account_settings_fields_spec.js',
        'lms/include/js/spec/student_account/account_settings_view_spec.js',
        'lms/include/js/spec/views/fields_spec.js',
        'lms/include/js/spec/student_profile/learner_profile_factory_spec.js',
        'lms/include/js/spec/student_profile/learner_profile_view_spec.js',
        'lms/include/js/spec/student_profile/learner_profile_fields_spec.js',
        'lms/include/js/spec/verify_student/pay_and_verify_view_spec.js',
        'lms/include/js/spec/verify_student/reverify_view_spec.js',
        'lms/include/js/spec/verify_student/webcam_photo_view_spec.js',
        'lms/include/js/spec/verify_student/image_input_spec.js',
        'lms/include/js/spec/verify_student/review_photos_step_view_spec.js',
        'lms/include/js/spec/verify_student/make_payment_step_view_spec.js',
        'lms/include/js/spec/edxnotes/utils/logger_spec.js',
        'lms/include/js/spec/edxnotes/views/notes_factory_spec.js',
        'lms/include/js/spec/edxnotes/views/shim_spec.js',
        'lms/include/js/spec/edxnotes/views/note_item_spec.js',
        'lms/include/js/spec/edxnotes/views/notes_page_spec.js',
        'lms/include/js/spec/edxnotes/views/search_box_spec.js',
        'lms/include/js/spec/edxnotes/views/tabs_list_spec.js',
        'lms/include/js/spec/edxnotes/views/tab_item_spec.js',
        'lms/include/js/spec/edxnotes/views/tab_view_spec.js',
        'lms/include/js/spec/edxnotes/views/tabs/search_results_spec.js',
        'lms/include/js/spec/edxnotes/views/tabs/recent_activity_spec.js',
        'lms/include/js/spec/edxnotes/views/tabs/course_structure_spec.js',
        'lms/include/js/spec/edxnotes/views/tabs/tags_spec.js',
        'lms/include/js/spec/edxnotes/views/visibility_decorator_spec.js',
        'lms/include/js/spec/edxnotes/views/notes_visibility_factory_spec.js',
        'lms/include/js/spec/edxnotes/models/tab_spec.js',
        'lms/include/js/spec/edxnotes/models/note_spec.js',
        'lms/include/js/spec/edxnotes/plugins/accessibility_spec.js',
        'lms/include/js/spec/edxnotes/plugins/events_spec.js',
        'lms/include/js/spec/edxnotes/plugins/scroller_spec.js',
        'lms/include/js/spec/edxnotes/plugins/caret_navigation_spec.js',
        'lms/include/js/spec/edxnotes/collections/notes_spec.js',
        'lms/include/js/spec/search/search_spec.js',
        'lms/include/js/spec/discovery/collections/filters_spec.js',
        'lms/include/js/spec/discovery/models/course_card_spec.js',
        'lms/include/js/spec/discovery/models/course_directory_spec.js',
        'lms/include/js/spec/discovery/models/facet_option_spec.js',
        'lms/include/js/spec/discovery/models/filter_spec.js',
        'lms/include/js/spec/discovery/models/search_state_spec.js',
        'lms/include/js/spec/discovery/views/course_card_spec.js',
        'lms/include/js/spec/discovery/views/courses_listing_spec.js',
        'lms/include/js/spec/discovery/views/filter_bar_spec.js',
        'lms/include/js/spec/discovery/views/refine_sidebar_spec.js',
        'lms/include/js/spec/discovery/views/search_form_spec.js',
        'lms/include/js/spec/discovery/discovery_factory_spec.js',
        'lms/include/js/spec/ccx/schedule_spec.js',
        'lms/include/support/js/spec/certificates_spec.js',
        'lms/include/teams/js/spec/collections/topic_collection_spec.js',
        'lms/include/teams/js/spec/teams_tab_factory_spec.js',
        'lms/include/teams/js/spec/views/edit_team_spec.js',
        'lms/include/teams/js/spec/views/edit_team_members_spec.js',
        'lms/include/teams/js/spec/views/instructor_tools_spec.js',
        'lms/include/teams/js/spec/views/my_teams_spec.js',
        'lms/include/teams/js/spec/views/team_card_spec.js',
        'lms/include/teams/js/spec/views/team_discussion_spec.js',
        'lms/include/teams/js/spec/views/team_profile_spec.js',
        'lms/include/teams/js/spec/views/teams_spec.js',
        'lms/include/teams/js/spec/views/teams_tab_spec.js',
        'lms/include/teams/js/spec/views/topic_card_spec.js',
        'lms/include/teams/js/spec/views/topic_teams_spec.js',
        'lms/include/teams/js/spec/views/topics_spec.js',
        'lms/include/teams/js/spec/views/team_profile_header_actions_spec.js'
    ]);

}).call(this, requirejs, define);
