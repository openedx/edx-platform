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

        model = new CourseDetailsModel();
        model.urlRoot = detailsUrl;
        model.showCertificateAvailableDate = showCertificateAvailableDate;
        model.set('upgrade_deadline', upgradeDeadline);
        model.fetch({
            success: function(model) {
                var editor = new MainView({
                    el: $('.settings-details'),
                    model: model,
                    showMinGradeWarning: showMinGradeWarning
                });
                editor.render();
            },
            reset: true
        });
    };
});
