define([
    'jquery', 'js/models/settings/course_details', 'js/views/settings/main',
    'js/common_helpers/ajax_helpers'
], function($, CourseDetailsModel, MainView, AjaxHelpers) {
    'use strict';
    describe('Settings/Main', function () {
        var urlRoot = '/course/settings/org/DemoX/Demo_Course',
            modelData = {
                start_date: "2014-10-05T00:00:00Z",
                end_date: "2014-11-05T20:00:00Z",
                enrollment_start: "2014-10-00T00:00:00Z",
                enrollment_end: "2014-11-05T00:00:00Z",
                org : '',
                course_id : '',
                run : '',
                syllabus : null,
                short_description : '',
                overview : '',
                intro_video : null,
                effort : null,
                course_image_name : '',
                course_image_asset_path : '',
                pre_requisite_courses : []
            },
            mockSettingsPage = readFixtures('mock/mock-settings-page.underscore');

        beforeEach(function () {
            setFixtures(mockSettingsPage);

            this.model = new CourseDetailsModel(modelData, {parse: true});
            this.model.urlRoot = urlRoot;
            this.view = new MainView({
                el: $('.settings-details'),
                model: this.model
            }).render();
        });

        afterEach(function () {
            // Clean up after the $.datepicker
            $("#start_date").datepicker("destroy");
            $("#due_date").datepicker("destroy");
            $('.ui-datepicker').remove();
        });

        it('Changing the time field do not affect other time fields', function () {
            var requests = AjaxHelpers.requests(this),
                expectedJson = $.extend(true, {}, modelData, {
                    // Expect to see changes just in `start_date` field.
                    start_date: "2014-10-05T22:00:00.000Z"
                });
            this.view.$el.find('#course-start-time')
                .val('22:00')
                .trigger('input');

            this.view.saveView();
            // It sends `POST` request, because the model doesn't have `id`. In
            // this case, it is considered to be new according to Backbone documentation.
            AjaxHelpers.expectJsonRequest(
                requests, 'POST', urlRoot, expectedJson
            );
        });

        it('Selecting a course in pre-requisite drop down should save it as part of course details', function () {
            var pre_requisite_courses = ['test/CSS101/2012_T1'];
            var requests = AjaxHelpers.requests(this),
                expectedJson = $.extend(true, {}, modelData, {
                    pre_requisite_courses: pre_requisite_courses
                });
            this.view.$el.find('#pre-requisite-course')
                .val(pre_requisite_courses[0])
                .trigger('change');

            this.view.saveView();
            AjaxHelpers.expectJsonRequest(
                requests, 'POST', urlRoot, expectedJson
            );
            AjaxHelpers.respondWithJson(requests, expectedJson);
        });
    });
});
