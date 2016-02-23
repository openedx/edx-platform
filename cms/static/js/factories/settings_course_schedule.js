define([
    'jquery', 'js/models/settings/course_schedule', 'js/views/settings/main'
], function($, CourseScheduleModel, MainView) {
    'use strict';
    return function (detailsUrl, showMinGradeWarning) {
        var model;
        debugger;
        // highlighting labels when fields are focused in
        $('form :input')
            .focus(function() {
                $('label[for="' + this.id + '"]').addClass('is-focused');
            })
            .blur(function() {
                $('label').removeClass('is-focused');
            });

        model = new CourseScheduleModel();
        model.urlRoot = detailsUrl;
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
