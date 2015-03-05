define([
    'jquery', 'js/models/settings/course_details', 'js/views/settings/main',
    'js/common_helpers/ajax_helpers'
], function($, CourseDetailsModel, MainView, AjaxHelpers) {
    'use strict';

    var SELECTORS = {
        entrance_exam_min_score: '#entrance-exam-minimum-score-pct',
        entrance_exam_enabled_field: '#entrance-exam-enabled',
        grade_requirement_div: '.div-grade-requirements div'
    };

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
                pre_requisite_courses : [],
                entrance_exam_enabled : '',
                entrance_exam_minimum_score_pct: '50',
                license: null
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

        it('should disallow save with an invalid minimum score percentage', function(){
            var entrance_exam_enabled_field = this.view.$(SELECTORS.entrance_exam_enabled_field),
                entrance_exam_min_score = this.view.$(SELECTORS.entrance_exam_min_score);

            //input some invalid values.
            expect(entrance_exam_min_score.val('101').trigger('input')).toHaveClass("error");
            expect(entrance_exam_min_score.val('invalidVal').trigger('input')).toHaveClass("error");

        });

        it('should provide a default value for the minimum score percentage', function(){

            var entrance_exam_min_score = this.view.$(SELECTORS.entrance_exam_min_score);

            //if input an empty value, model should be populated with the default value.
            entrance_exam_min_score.val('').trigger('input');
            expect(this.model.get('entrance_exam_minimum_score_pct'))
                .toEqual(this.model.defaults.entrance_exam_minimum_score_pct);
        });

        it('show and hide the grade requirement section when the check box is selected and deselected respectively', function(){

            var entrance_exam_enabled_field = this.view.$(SELECTORS.entrance_exam_enabled_field);

            // select the entrance-exam-enabled checkbox. grade requirement section should be visible.
            entrance_exam_enabled_field
                .attr('checked', 'true')
                .trigger('change');

            this.view.render();
            expect(this.view.$(SELECTORS.grade_requirement_div)).toBeVisible();

            // deselect the entrance-exam-enabled checkbox. grade requirement section should be hidden.
            entrance_exam_enabled_field
                .removeAttr('checked')
                .trigger('change');

            expect(this.view.$(SELECTORS.grade_requirement_div)).toBeHidden();

        });

        it('should save entrance exam course details information correctly', function () {
            var entrance_exam_minimum_score_pct = '60',
                entrance_exam_enabled = 'true',
                entrance_exam_min_score = this.view.$(SELECTORS.entrance_exam_min_score),
                entrance_exam_enabled_field = this.view.$(SELECTORS.entrance_exam_enabled_field);

            var requests = AjaxHelpers.requests(this),
                expectedJson = $.extend(true, {}, modelData, {
                    entrance_exam_enabled: entrance_exam_enabled,
                    entrance_exam_minimum_score_pct: entrance_exam_minimum_score_pct
                });

            // select the entrance-exam-enabled checkbox.
            entrance_exam_enabled_field
                .attr('checked', 'true')
                .trigger('change');

            // input a valid value for entrance exam minimum score.
            entrance_exam_min_score.val(entrance_exam_minimum_score_pct).trigger('input');

            this.view.saveView();
            AjaxHelpers.expectJsonRequest(
                requests, 'POST', urlRoot, expectedJson
            );
            AjaxHelpers.respondWithJson(requests, expectedJson);
        });
    });
});
