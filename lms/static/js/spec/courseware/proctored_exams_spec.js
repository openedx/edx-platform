define(['jquery', 'backbone', 'common/js/spec_helpers/template_helpers', 'js/courseware/base/models/proctored_exam_model', 'js/courseware/base/views/proctored_exam_view'
], function($, Backbone, TemplateHelpers, ProctoredExamModel, ProctoredExamView) {
    'use strict';

    describe('Proctored Exam', function () {

        beforeEach(function () {
            this.model = new ProctoredExamModel();
        });

        it('model has properties', function () {
            expect(this.model.get('in_timed_exam')).toBeDefined();
            expect(this.model.get('is_proctored')).toBeDefined();
            expect(this.model.get('exam_display_name')).toBeDefined();
            expect(this.model.get('exam_url_path')).toBeDefined();
            expect(this.model.get('time_remaining_seconds')).toBeDefined();
            expect(this.model.get('low_threshold')).toBeDefined();
            expect(this.model.get('critically_low_threshold')).toBeDefined();
            expect(this.model.get('lastFetched')).toBeDefined();
        });

    });

    describe('ProctoredExamView', function () {
        beforeEach(function () {
            TemplateHelpers.installTemplate('templates/courseware/proctored-exam-status', true, 'proctored-exam-status-tpl');
            appendSetFixtures('<div class="proctored_exam_status"></div>');

            this.model = new ProctoredExamModel({
                in_timed_exam: true,
                is_proctored: true,
                exam_display_name: 'Midterm',
                exam_url_path: '/test_url',
                time_remaining_seconds: 45, //2 * 60 + 15,
                low_threshold: 30,
                critically_low_threshold: 15,
                lastFetched: new Date()
            });

            this.proctored_exam_view = new edx.coursware.proctored_exam.ProctoredExamView(
                {
                    model: this.model,
                    el: $(".proctored_exam_status"),
                    proctored_template: '#proctored-exam-status-tpl'
                }
            );
            this.proctored_exam_view.render();
        });

        it('renders items correctly', function () {
            expect(this.proctored_exam_view.$el.find('a')).toHaveAttr('href',  this.model.get("exam_url_path"));
            expect(this.proctored_exam_view.$el.find('a')).toContainHtml(this.model.get('exam_display_name'));
        });
        it('changes behavior when clock time decreases low threshold', function () {
            spyOn(this.model, 'getRemainingSeconds').andCallFake(function () {
                return 25;
            });
            expect(this.model.getRemainingSeconds()).toEqual(25);
            expect(this.proctored_exam_view.$el.find('div.exam-timer')).not.toHaveClass('low-time warning');
            this.proctored_exam_view.render();
            expect(this.proctored_exam_view.$el.find('div.exam-timer')).toHaveClass('low-time warning');
        });
        it('changes behavior when clock time decreases critically low threshold', function () {
            spyOn(this.model, 'getRemainingSeconds').andCallFake(function () {
                return 5;
            });
            expect(this.model.getRemainingSeconds()).toEqual(5);
            expect(this.proctored_exam_view.$el.find('div.exam-timer')).not.toHaveClass('low-time critical');
            this.proctored_exam_view.render();
            expect(this.proctored_exam_view.$el.find('div.exam-timer')).toHaveClass('low-time critical');
        });
    });
});
