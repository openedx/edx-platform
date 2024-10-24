define([
    'jquery', 'js/models/settings/course_details', 'js/views/settings/main'
], function($, CourseDetailsModel, MainView) {
    'use strict';

    return function(detailsUrl, showMinGradeWarning, showCertificateAvailableDate, upgradeDeadline) {
        var model;
        // highlighting labels when fields are focused in
        $('form :input')
            .focus(function() {
                $('label[for="' + this.id + '"]').addClass('is-focused');
            })
            .blur(function() {
                $('label').removeClass('is-focused');
            });

        // Toggle collapsibles when trigger is clicked
        $('.collapsible .collapsible-trigger').click(function() {
            const contentId = this.id.replace('-trigger', '-content');
            $(`#${contentId}`).toggleClass('collapsed');
        });

        model = new CourseDetailsModel();
        model.urlRoot = detailsUrl;
        model.showCertificateAvailableDate = showCertificateAvailableDate;
        model.set('upgrade_deadline', upgradeDeadline);
        model.fetch({
            // eslint-disable-next-line no-shadow
            success: function(model) {
                var editor = new MainView({
                    el: $('.settings-details'),
                    model: model,
                    showMinGradeWarning: showMinGradeWarning
                });
                editor.render();
            },
            reset: true,
            cache: false
        });
    };
});
