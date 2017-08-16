(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils
         ) {
             return Backbone.View.extend({
                 el: '.unenroll-modal',

                 unenrollClick: function(event) {
                     var isPaidCourse = $(event.target).data('course-is-paid-course') === 'True',
                         certNameLong = $(event.target).data('course-cert-name-long'),
                         enrollmentMode = $(event.target).data('course-enrollment-mode'),
                         courseNumber = $(event.target).data('course-number'),
                         courseName = $(event.target).data('course-name'),
                         courseRefundUrl = $(event.target).data('course-refund-url'),
                         dialogMessageAttr,
                         request = $.ajax({
                             url: courseRefundUrl,
                             method: 'GET',
                             dataType: 'json'
                         });
                     request.success(function(data, textStatus, xhr) {
                         if (xhr.status === 200) {
                             dialogMessageAttr = setDialogAttributes(isPaidCourse, certNameLong,
                                            courseNumber, courseName, enrollmentMode, data.course_refundable_status);

                             $('#track-info').empty();
                             $('#refund-info').empty();

                             $('#track-info').html(interpolate(dialogMessageAttr['data-track-info'], {
                                 courseNumber: ['<span id="unenroll_course_number">', courseNumber, '</span>'].join(''),
                                 courseName: ['<span id="unenroll_course_name">', courseName, '</span>'].join(''),
                                 certNameLong: ['<span id="unenroll_cert_name">', certNameLong, '</span>'].join('')
                             }, true));


                             if ('data-refund-info' in dialogMessageAttr) {
                                 $('#refund-info').text(dialogMessageAttr['data-refund-info']);
                             }

                             $('#unenroll_course_id').val($(event.target).data('course-id'));
                         } else {
                             $('#unenroll_error').text(
                                gettext('Unable to determine whether we should give you a refund because' +
                                        ' of System Error. Please try again later.')
                             ).stop()
                              .css('display', 'block');

                             $('#unenroll_form input[type="submit"]').prop('disabled', true);
                         }
                         edx.dashboard.dropdown.toggleCourseActionsDropdownMenu(event);
                     });
                     request.fail(function() {
                         $('#unenroll_error').text(
                                gettext('Unable to determine whether we should give you a refund because' +
                                        ' of System Error. Please try again later.')
                         ).stop()
                          .css('display', 'block');

                         $('#unenroll_form input[type="submit"]').prop('disabled', true);

                         edx.dashboard.dropdown.toggleCourseActionsDropdownMenu(event);
                     });

                     // Randomize survey option order
                     survey = document.querySelector('.options');
                     for (i = survey.children.length - 1; i >= 0; i--) {
                         survey.appendChild(survey.children[Math.random() * i | 0]);
                     }
                 },

                 function setDialogAttributes(isPaidCourse, certNameLong,
                                        courseNumber, courseName, enrollmentMode, showRefundOption) {
                     var diagAttr = {};

                     if (isPaidCourse) {
                         if (showRefundOption) {
                             diagAttr['data-refund-info'] = gettext('You will be refunded the amount you paid.');
                         } else {
                             diagAttr['data-refund-info'] = gettext('You will not be refunded the amount you paid.');
                         }
                         diagAttr['data-track-info'] = gettext('Are you sure you want to unenroll from the purchased course ' +
                                                           '%(courseName)s (%(courseNumber)s)?');
                     } else if (enrollmentMode !== 'verified') {
                         diagAttr['data-track-info'] = gettext('Are you sure you want to unenroll from %(courseName)s ' +
                                                           '(%(courseNumber)s)?');
                     } else if (showRefundOption) {
                         diagAttr['data-track-info'] = gettext('Are you sure you want to unenroll from the verified ' +
                                                           '%(certNameLong)s  track of %(courseName)s  (%(courseNumber)s)?');
                         diagAttr['data-refund-info'] = gettext('You will be refunded the amount you paid.');
                     } else {
                         diagAttr['data-track-info'] = gettext('Are you sure you want to unenroll from the verified ' +
                                                           '%(certNameLong)s track of %(courseName)s (%(courseNumber)s)?');
                         diagAttr['data-refund-info'] = gettext('The refund deadline for this course has passed,' +
                             'so you will not receive a refund.');
                     }

                     return diagAttr;
                 },

                 switchToSlideOne: function() {
                     var reasonsSurvey = HtmlUtils.HTML($('.reasons_survey'));
                     $('.inner-wrapper header').hide();
                     $('#unenroll_form').after(HtmlUtils.ensureHtml(reasonsSurvey).toString()).hide();
                     $('.reasons_survey .slide1').removeClass('hidden');
                 },

                 switchToSlideTwo: function() {
                     var reason = $(".reasons_survey input[name='reason']:checked").attr('val');
                     if (reason === 'Other') {
                         reason = $('.other_text').val();
                     }
                     if (reason) {
                         window.analytics.track('unenrollment_reason.selected', {
                             category: 'user-engagement',
                             label: reason,
                             displayName: 'v1'
                         });
                     }
                     HtmlUtils.setHtml($('.reasons_survey'), HtmlUtils.HTML($('.slide2').html()));
                     $('.reasons_survey .return_to_dashboard').attr('href', this.urls.dashboard);
                     $('.reasons_survey .browse_courses').attr('href', this.urls.browseCourses);
                 },

                 unenrollComplete: function(event, xhr) {
                     if (xhr.status === 200) {
                         this.switchToSlideOne();
                         $('.submit_reasons').click(this.switchToSlideTwo.bind(this));
                     } else if (xhr.status === 403) {
                         location.href = this.urls.signInUser + '?course_id=' +
                        encodeURIComponent($('#unenroll_course_id').val()) + '&enrollment_action=unenroll';
                     } else {
                         $('#unenroll_error').text(
                         gettext('Unable to determine whether we should give you a refund because' +
                                ' of System Error. Please try again later.')
                         ).stop()
                          .css('display', 'block');
                         }
                 },

                 initialize: function(options) {
                     this.urls = options.urls;

                     $('.action-unenroll').click(this.unenrollClick);

                     $('#unenroll_form').on('ajax:complete', this.unenrollComplete.bind(this));

                     $('#unregister_block_course').click(function(event) {
                         $('#unenroll_course_id').val($(event.target).data('course-id'));
                         $('#unenroll_course_number').text($(event.target).data('course-number'));
                         $('#unenroll_course_name').text($(event.target).data('course-name'));
                     });
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
