define([
    'jquery', 'js/models/settings/course_details', 'js/views/settings/main'
], function($, CourseDetailsModel, MainView) {
    'use strict';

<<<<<<< HEAD
    return function(detailsUrl, showMinGradeWarning, showCertificateAvailableDate, upgradeDeadline, useV2CertDisplaySettings) {
=======
    return function(detailsUrl, showMinGradeWarning, showCertificateAvailableDate, upgradeDeadline) {
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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
<<<<<<< HEAD
        model.useV2CertDisplaySettings = useV2CertDisplaySettings;
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        model.set('upgrade_deadline', upgradeDeadline);
        model.fetch({
            // eslint-disable-next-line no-shadow
            success: function(model) {
                var editor = new MainView({
                    el: $('.settings-details'),
                    model: model,
                    showMinGradeWarning: showMinGradeWarning
                });
<<<<<<< HEAD
                editor.useV2CertDisplaySettings = useV2CertDisplaySettings;
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                editor.render();
            },
            reset: true,
            cache: false
        });
    };
});
