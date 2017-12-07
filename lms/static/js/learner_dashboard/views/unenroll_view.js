(function(define, accessibleModal) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils'
        ],
        function(Backbone, $, _, gettext, HtmlUtils) {
            return Backbone.View.extend({
                el: '#unenroll-modal',

                initialize: function(options) {
                    var view = this;

                    this.$error_info = this.$el.find('#unenroll_error');
                    this.$track_info = this.$el.find('#track-info');
                    this.$refund_info = this.$el.find('#refund-info');
                    this.$form = this.$el.find('#unenroll_form');

                    this.urls = options.urls;
                    this.isEdx = options.isEdx;
                    this.$form.on('ajax:complete', this.unenrollComplete.bind(this));

                    // Configure each of the unenroll links to work with the modal.
                    $('.action-unenroll').each(function(index) {
                        var $link = $(this);

                        $link.on('click', view.renderModal.bind(view));

                        // Necessary for modal a11y functionality
                        // Seems to need to be called AFTER the renderModal listeners have been set on the link.
                        accessibleModal(
                           '#' + $link.attr('id'), // Selector for the element that triggered the modal
                           '#unenroll-modal .close-modal', // Selector for the close button
                           '#unenroll-modal', // Selector for the modal
                           '#dashboard-main' // Selector for the main page content
                        );
                    });
                },

                renderModal: function(event) {
                    this.resetModal();
                    this.renderModalForCourserun(event);

                    // Unfortunately, the method for closing the gear dropdown is defined globally.
                    if (edx && edx.dashboard && edx.dashboard.dropdown) {
                        edx.dashboard.dropdown.toggleCourseActionsDropdownMenu(event);
                    }
                    this.$el.css('position', 'fixed');
                },

                resetModal: function() {
                    this.$refund_info.empty();
                    this.$track_info.empty();
                    this.$error_info.empty();
                    this.$el.find('#unenroll_course_id').empty();
                },

                renderModalForCourserun: function(event) {
                    var $link = $(event.target),
                        isPaidCourse = $link.data('course-is-paid-course') === 'True',
                        certNameLong = $link.data('course-cert-name-long'),
                        enrollmentMode = $link.data('course-enrollment-mode'),
                        courseId = $link.data('course-id'),
                        courseNumber = $link.data('course-number'),
                        courseName = $link.data('course-name'),
                        courseRefundUrl = $link.data('course-refund-url'),

                        successHandler = function(data, textStatus, xhr) {
                            if (xhr.status === 200) {
                                this.setModalTextForCourserun(isPaidCourse, certNameLong, courseNumber, courseName, enrollmentMode, data.course_refundable_status);
                                this.$el.find('#unenroll_course_id').val(courseId);
                            } else {
                                errorHandler();
                            }
                        };

                    // Make a request to the refund_status API to determine whether or not this courseRun is refundable.
                    $.ajax({
                        url: courseRefundUrl,
                        method: 'GET',
                        dataType: 'json',
                        success: successHandler.bind(this),
                        fail: this.setModalErrorTextForCourserun.bind(this)
                    });
                },

                setModalErrorTextForCourserun: function() {
                    this.$error_info.empty();
                    HtmlUtils.setHtml(
                        this.$error_info,
                        gettext('Unable to determine whether we should give you a refund because of System Error. Please try again later.')
                    );
                    this.$error_info.stop().css('display', 'block');

                    this.$form.find('input[type="submit"]').prop('disabled', true);
                },

                setModalTextForCourserun: function(isPaidCourse, certNameLong, courseNumber, courseName, enrollmentMode, isCourseRefundable) {
                    var modalText = this.getModalTextForCourserun(isPaidCourse, certNameLong, courseNumber, courseName, enrollmentMode, isCourseRefundable);

                    this.$track_info.empty();
                    HtmlUtils.setHtml(
                        this.$track_info,
                        HtmlUtils.interpolateHtml(
                            modalText['track-info'],
                            {
                                courseNumber: HtmlUtils.joinHtml(
                                    HtmlUtils.HTML('<span id="unenroll_course_number">'),
                                    courseNumber,
                                    HtmlUtils.HTML('</span>')
                                ),
                                courseName: HtmlUtils.joinHtml(
                                    HtmlUtils.HTML('<span id="unenroll_course_name">'),
                                    courseName,
                                    HtmlUtils.HTML('</span>')
                                ),
                                certNameLong: HtmlUtils.joinHtml(
                                    HtmlUtils.HTML('<span id="unenroll_cert_name">'),
                                    certNameLong,
                                    HtmlUtils.HTML('</span>')
                                )
                            }
                        )
                    );

                    this.$refund_info.empty();
                    if ('refund-info' in modalText) {
                        HtmlUtils.setHtml(
                            this.$refund_info,
                            modalText['refund-info']
                        );
                    }
                },

                getModalTextForCourserun: function (isPaidCourse, certNameLong, courseNumber, courseName, enrollmentMode, showRefundOption) {
                    var text = {};

                    if (isPaidCourse) {
                        if (showRefundOption) {
                            text['refund-info'] = gettext('You will be refunded the amount you paid.');
                        } else {
                            text['refund-info'] = gettext('You will not be refunded the amount you paid.');
                        }
                        text['track-info'] = gettext('Are you sure you want to unenroll from the purchased course {courseName} ({courseNumber})?');
                    } else if (enrollmentMode !== 'verified') {
                        text['track-info'] = gettext('Are you sure you want to unenroll from {courseName} ({courseNumber})?');
                    } else if (showRefundOption) {
                        text['track-info'] = gettext('Are you sure you want to unenroll from the verified {certNameLong} track of {courseName} ({courseNumber})?');
                        text['refund-info'] = gettext('You will be refunded the amount you paid.');
                    } else {
                        text['track-info'] = gettext('Are you sure you want to unenroll from the verified {certNameLong} track of {courseName} ({courseNumber})?');
                        text['refund-info'] = gettext('The refund deadline for this course has passed, so you will not receive a refund.');
                    }

                    return text;
                },

                switchToSlideOne: function() {
                    var survey, i;
                    // Randomize survey option order
                    survey = document.querySelector('.options');
                    for (i = survey.children.length - 1; i >= 0; i--) {
                        survey.appendChild(survey.children[Math.random() * i | 0]);
                    }
                    this.$('.inner-wrapper header').hide();
                    this.$form.hide();
                    this.$('.slide1').removeClass('hidden');
                },

                switchToSlideTwo: function() {
                    var reason = this.$(".reasons_survey input[name='reason']:checked").attr('val');
                    if (reason === 'Other') {
                        reason = this.$('.other_text').val();
                    }
                    if (reason) {
                        window.analytics.track('unenrollment_reason.selected', {
                            category: 'user-engagement',
                            label: reason,
                            displayName: 'v1'
                        });
                    }
                    this.$('.slide1').addClass('hidden');
                    this.$('.survey_course_name').text(this.$('#unenroll_course_name').text());
                    this.$('.slide2').removeClass('hidden');
                    this.$('.reasons_survey .return_to_dashboard').attr('href', this.urls.dashboard);
                    this.$('.reasons_survey .browse_courses').attr('href', this.urls.browseCourses);
                },

                unenrollComplete: function(event, xhr) {
                    if (xhr.status === 200) {
                        if (!this.isEdx) {
                            location.href = this.urls.dashboard;
                        } else {
                            this.switchToSlideOne();
                            this.$('.reasons_survey:first .submit_reasons').click(this.switchToSlideTwo.bind(this));
                        }
                    } else if (xhr.status === 403) {
                        location.href = this.urls.signInUser + '?course_id=' +
                        encodeURIComponent($('#unenroll_course_id').val()) + '&enrollment_action=unenroll';
                    } else {
                        this.setModalErrorTextForCourserun();
                    }
                }

            });
        }
    );
}).call(this, define || RequireJS.define, accessible_modal);
