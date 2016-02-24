define([
    'jquery', 'js/models/settings/course_schedule', 'js/views/settings/course_schedule'
], function($, CourseScheduleModel, ScheduleView) {
    'use strict';
    return function (detailsUrl, showMinGradeWarning) {
        var model;
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
                var editor = new ScheduleView({
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
