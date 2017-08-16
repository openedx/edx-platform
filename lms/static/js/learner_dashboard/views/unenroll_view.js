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

                 switchToSlideOne: function() {
                     var survey, i,
                         reasonsSurvey = HtmlUtils.HTML($('.reasons_survey'));
                     // Randomize survey option order
                     survey = document.querySelector('.options');
                     for (i = survey.children.length - 1; i >= 0; i--) {
                         survey.appendChild(survey.children[Math.random() * i | 0]);
                     }
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
                         if (!this.isEdx) {
                             location.href = this.urls.dashboard;
                         } else {
                             this.switchToSlideOne();
                             $('.submit_reasons').click(this.switchToSlideTwo.bind(this));
                         }
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
                     this.isEdx = options.isEdx;

                     $('#unenroll_form').on('ajax:complete', this.unenrollComplete.bind(this));
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
