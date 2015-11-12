;(function (define, accessibleModal) {
    'use strict';

    define(['jquery',
            'backbone',
            'underscore',
            'underscore.string',
            'text!templates/dashboard/course.underscore',
            'text!templates/dashboard/certificate_info.underscore',
            'text!templates/dashboard/credit_info.underscore',
            'text!templates/dashboard/course_verification_info.underscore',
            'text!templates/dashboard/course_mode_info.underscore',
            'text!templates/dashboard/programs_info.underscore'],
        function ($,
                  Backbone,
                  _,
                  _s,
                  courseTemplate,
                  certInfoTemplate,
                  creditInfoTemplate,
                  courseVerificationInfoTemplate,
                  courseModeInfoTemplate,
                  programsInfoTemplate) {

            if (_.isUndefined(_s)) {
                _s = _.str;
            }

            var CourseView = Backbone.View.extend({
                tagName: 'li',
                className: 'course-item',
                template: _.template(courseTemplate),
                certTemplate: _.template(certInfoTemplate),
                creditTemplate: _.template(creditInfoTemplate),
                courseVerificationTemplate: _.template(courseVerificationInfoTemplate),
                courseModeTemplate: _.template(courseModeInfoTemplate),
                programsTemplate: _.template(programsInfoTemplate),

                events: {
                    'click .action-more': 'toggleCourseActionsDropDown',
                    'click .action-unenroll': 'unEnroll',
                    'click .action-email-settings': 'emailSettings',
                    'click #upgrade-to-verified': 'upgradeToVerified',
                    'click #block-course-msg a[rel="leanModal"]': 'unRegisterBlockCourse',
                    'ajax:complete #unenroll_form': 'unEnrollFormSubmitted',
                    'submit #email_settings_form': 'submitEmailSettingsForm'
                },

                initialize: function (options) {
                    this.settings = options.settings;

                    /* Mix non-conflicting functions from underscore.string
                     * (all but include, contains, and reverse) into the
                     * Underscore namespace
                     */
                    _.mixin(_s.exports());
                },

                render: function () {
                    this.$el.html(this.template({model: this.model.attributes, settings: this.settings}));
                    this.$("#certificate-info-section").replaceWith(
                        this.certTemplate({model: this.model.attributes, settings: this.settings})
                    );
                    this.$("#credit-info-section").replaceWith(
                        this.creditTemplate({model: this.model.attributes, settings: this.settings})
                    );
                    this.$("#course-verification-info-section").replaceWith(
                        this.courseVerificationTemplate({model: this.model.attributes, settings: this.settings})
                    );
                    this.$("#course-mode-info-section").replaceWith(
                        this.courseModeTemplate({model: this.model.attributes, settings: this.settings})
                    );
                    this.$("#programs-info-section").replaceWith(
                        this.programsTemplate({model: this.model.attributes, settings: this.settings})
                    );
                    var $actionUnroll = this.$('.action-unenroll'),
                        $unRegisterBlockCourse = this.$('#unregister_block_course'),
                        $actionEmailSettings = this.$('.action-email-settings'),
                        modalType = {
                            unenroll: 'unenroll',
                            emailSettings: 'email-settings'
                        };

                    this.bindModal($actionUnroll, modalType.unenroll);
                    this.bindModal($unRegisterBlockCourse, modalType.unenroll);
                    this.bindModal($actionEmailSettings, modalType.emailSettings);

                    return this;
                },

                bindModal: function ($selector, type) {
                    var trigger,
                        id = _.uniqueId('lean-modal-');

                    $selector.attr('id', id);
                    trigger = '#' + id;

                    this.$(trigger).leanModal({
                        overlay: 1,
                        closeButton: '.close-modal'
                    });

                    accessibleModal(
                        trigger,
                        _.sprintf('.%(type)s-modal .close-modal', {type: type}),
                        _.sprintf('.%(type)s-modal', {type: type}),
                        '#dashboard-main'
                    );
                },

                toggleCourseActionsDropDown: function (e) {
                    // Suppress the actual click event from the browser
                    e.preventDefault();

                    var ariaExpandedState,
                        $currentTarget = this.$(e.currentTarget),
                    // Toggle the visibility control for the selected element and set the focus
                        $dropDown = this.$('div#actions-dropdown');

                    if ($dropDown.hasClass('is-visible')) {
                        $dropDown.attr('tabindex', -1);
                    } else {
                        $dropDown.removeAttr('tabindex');
                    }

                    $dropDown.toggleClass('is-visible');

                    // Inform the ARIA framework that the dropdown has been expanded
                    ariaExpandedState = ($currentTarget.attr('aria-expanded') === 'true');
                    $currentTarget.attr('aria-expanded', !ariaExpandedState);
                },

                unEnroll: function (e) {
                    var $currentTarget = this.$(e.currentTarget),
                        track_info = $currentTarget.data('track-info'),
                        courseId = $currentTarget.data('course-id'),
                        courseNumber = $currentTarget.data('course-number'),
                        courseName = $currentTarget.data('course-name'),
                        certNameLang = $currentTarget.data('cert-name-long'),
                        refundInfo = $currentTarget.data('refund-info');

                    $('#track-info').html(_.sprintf(track_info, {
                        course_number: _.sprintf(
                            '<span id="unenroll_course_number">%(courseNumber)s</span>', {courseNumber: courseNumber}
                        ),
                        course_name: _.sprintf(
                            '<span id="unenroll_course_name">%(courseName)s</span>', {courseName: courseName}
                        ),
                        cert_name_long: _.sprintf(
                            '<span id="unenroll_cert_name">%(certNameLang)s</span>', {certNameLang: certNameLang}
                        )
                    }, true));

                    $('#refund-info').html(refundInfo);
                    $('#unenroll_course_id').val(courseId);
                },

                emailSettings: function (e) {
                    var $currentTarget = this.$(e.currentTarget);

                    $('#email_settings_course_id').val($currentTarget.data('course-id'));
                    $('#email_settings_course_number').text($currentTarget.data('course-number'));

                    if ($currentTarget.data('optout') === 'False') {
                        $('#receive_emails').prop('checked', true);
                    }
                },

                upgradeToVerified: function (e) {
                    var $currentTarget = this.$(e.currentTarget);
                    $currentTarget.closest('.action-upgrade').data('user');
                    $currentTarget.closest('.action-upgrade').data('course-id');
                },

                unRegisterBlockCourse: function (e) {
                    var $currentTarget = this.$(e.currentTarget),
                        courseId = $currentTarget.data('course-id'),
                        courseNumber = $currentTarget.data('course-number'),
                        courseName = $currentTarget.data('course-name');

                    if (this.$('#block-course-msg').length) {
                        $('.disable-look-unregister').click();
                    }

                    $('#track-info').html(_.sprintf(
                        '<span id="unenroll_course_number">%(courseNumber)s</span> ' +
                        '- <span id="unenroll_course_name">%(courseName)s?</span>',
                        {courseNumber: courseNumber, courseName: courseName})
                    );

                    $('#unenroll_course_id').val(courseId);
                },

                unEnrollFormSubmitted: function (e, xhr) {
                    if (xhr.status === 200) {
                        location.href = this.settings.dashboard;
                    } else if (xhr.status === 403) {
                        location.href = this.settings.signin_user + "?course_id=" +
                            encodeURIComponent(this.$("#unenroll_course_id").val()) + "&enrollment_action=unenroll";
                    } else {
                        $('#unenroll_error').html(
                            xhr.responseText ? xhr.responseText : gettext("An error occurred. Please try again later.")
                        ).stop().css("display", "block");
                    }
                },

                submitEmailSettingsForm: function (e) {

                    e.preventDefault();

                    $.ajax({
                        context: this,
                        type: "POST",
                        url: this.settings.change_email_settings,
                        data: this.$(e.target).serializeArray(),
                        success: function (data) {
                            if (data.success) {
                                location.href = this.settings.dashboard;
                            }
                        },
                        error: function (xhr) {
                            if (xhr.status === 403) {
                                location.href = this.settings.signin_user;
                            }
                        }
                    });
                }
            });

            return CourseView;
        });

}).call(this, define || RequireJS.define, accessible_modal); // jshint undef:false
