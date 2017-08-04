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
                     var $element = $(event.target),
                         trackInfo = $element.data('track-info'),
                         courseNumber = $element.data('course-number'),
                         courseName = $element.data('course-name'),
                         certNameLong = $element.data('cert-name-long'),
                         survey, i;

                     $('.action-unenroll').each(function(index) {
                         var id = 'unenroll-' + index,
                             trigger = '#' + id;
                         $(this).attr('id', id);
                         window.accessible_modal(
                            trigger,
                            '#unenroll-modal .close-modal',
                            '#unenroll-modal',
                            '#dashboard-main'
                         );
                     });

                     HtmlUtils.setHtml(
                         $('#track-info'), HtmlUtils.HTML(window.interpolate(trackInfo, {
                             course_number: HtmlUtils.joinHtml(
                                HtmlUtils.HTML("<span id='unenroll_course_number'>"),
                                courseNumber,
                                HtmlUtils.HTML('</span>')
                             ),
                             course_name: HtmlUtils.joinHtml(
                                HtmlUtils.HTML("<span id='unenroll_course_name'>"),
                                courseName,
                                HtmlUtils.HTML('</span>')
                             ),
                             cert_name_long: HtmlUtils.joinHtml(
                                HtmlUtils.HTML("<span id='unenroll_cert_name'>"),
                                certNameLong,
                                HtmlUtils.HTML('</span>')
                             )
                         }, true))
                     );
                     HtmlUtils.setHtml(
                         $('#refund-info'), HtmlUtils.HTML($element.data('refund-info'))
                     );
                     $('#unenroll_course_id').val($element.data('course-id'));

                     // Randomize survey option order
                     survey = document.querySelector('.options');
                     for (i = survey.children.length - 1; i >= 0; i--) {
                         survey.appendChild(survey.children[Math.random() * i | 0]);
                     }
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
                     var errorText;
                     if (xhr.status === 200) {
                         this.switchToSlideOne();
                         $('.submit_reasons').click(this.switchToSlideTwo.bind(this));
                     } else if (xhr.status === 403) {
                         location.href = this.urls.signInUser + '?course_id=' +
                        encodeURIComponent($('#unenroll_course_id').val()) + '&enrollment_action=unenroll';
                     } else {
                         errorText = gettext('An error occurred. Please try again later.');
                         $('#unenroll_error').html(xhr.responseText ? xhr.responseText : errorText)
                         .stop()
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
