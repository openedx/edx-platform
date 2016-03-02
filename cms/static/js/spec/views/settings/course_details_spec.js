define([
    'jquery', 'js/models/settings/course_details', 'js/views/settings/course_details',
    'common/js/spec_helpers/ajax_helpers'
], function($, CourseDetailsModel, CourseDetailsView, AjaxHelpers) {
    'use strict';

    describe('Settings/CourseDetails', function () {
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
                license: null,
                language: ''
            },
            mockSettingsPage = readFixtures('mock/mock-settings-page.underscore');

        beforeEach(function () {
            setFixtures(mockSettingsPage);

            this.model = new CourseDetailsModel(modelData, {parse: true});
            this.model.urlRoot = urlRoot;
            this.view = new CourseDetailsView({
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

        it('should save language as part of course details', function(){
            var requests = AjaxHelpers.requests(this);
            var expectedJson = $.extend(true, {}, modelData, {language: 'en'});
            $('#course-language').val('en').trigger('change');
            expect(this.model.get('language')).toEqual('en');
            this.view.saveView();
            AjaxHelpers.expectJsonRequest(
                requests, 'POST', urlRoot, expectedJson
            );
        });

    });
});
