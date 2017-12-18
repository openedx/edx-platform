define([
    'backbone',
    'jquery',
    'edx-ui-toolkit/js/utils/spec-helpers/spec-helpers',
    'common/js/components/views/progress_circle_view'
], function(Backbone, $, SpecHelpers, ProgressCircleView) {
    'use strict';

    describe('Progress Circle View', function() {
        var view = null,
            context = {
                title: 'XSeries Progress',
                label: 'Earned Certificates',
                progress: {
                    completed: 2,
                    in_progress: 1,
                    not_started: 3
                }
            },
            testCircle,
            testText,
            initView,
            getProgress,
            testProgress;

        testCircle = function(progress) {
            var $circle = view.$('.progress-circle');

            expect($circle.find('.complete').length).toEqual(progress.completed);
            expect($circle.find('.incomplete').length).toEqual(progress.in_progress + progress.not_started);
        };

        testText = function(progress) {
            var $numbers = view.$('.numbers'),
                total = progress.completed + progress.in_progress + progress.not_started;

            expect(view.$('.progress-heading').html()).toEqual('XSeries Progress');
            expect(parseInt($numbers.find('.complete').html(), 10)).toEqual(progress.completed);
            expect(parseInt($numbers.find('.total').html(), 10)).toEqual(total);
        };

        getProgress = function(x, y, z) {
            return {
                completed: x,
                in_progress: y,
                not_started: z
            };
        };

        testProgress = function(x, y, z) {
            var progress = getProgress(x, y, z);

            view = initView(progress);
            view.render();

            testCircle(progress);
            testText(progress);
        };

        initView = function(progress) {
            var data = $.extend({}, context, {
                progress: progress
            });

            return new ProgressCircleView({
                el: '.js-program-progress',
                model: new Backbone.Model(data)
            });
        };

        beforeEach(function() {
            setFixtures('<div class="js-program-progress"></div>');
        });

        afterEach(function() {
            view.remove();
        });

        it('should exist', function() {
            var progress = getProgress(2, 1, 3);

            view = initView(progress);
            view.render();
            expect(view).toBeDefined();
        });

        it('should render the progress circle based on the passed in model', function() {
            var progress = getProgress(2, 1, 3);

            view = initView(progress);
            view.render();
            testCircle(progress);
        });

        it('should render the progress text based on the passed in model', function() {
            var progress = getProgress(2, 1, 3);

            view = initView(progress);
            view.render();
            testText(progress);
        });

        SpecHelpers.withData({
            'should render the progress text with only completed courses': [5, 0, 0],
            'should render the progress text with only in progress courses': [0, 4, 0],
            'should render the progress circle with only not started courses': [0, 0, 5],
            'should render the progress text with no completed courses': [0, 2, 3],
            'should render the progress text with no in progress courses': [2, 0, 7],
            'should render the progress text with no not started courses': [2, 4, 0]
        }, testProgress);
    });
});
