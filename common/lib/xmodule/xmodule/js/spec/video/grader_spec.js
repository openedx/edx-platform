(function (require) {
'use strict';
require(
['video/11_grader.js', 'video/00_i18n.js', 'video/00_abstract_grader.js'],
function (Grader, i18n, AbstractGrader) {
describe('VideoGrader', function () {
    var SCORED_TEXT = '(0.5 / 1.0 points)',
        POSSIBLE_SCORES = '1.0 points possible',
        SUCCESS_MESSAGE = 'You\'ve received credit for viewing this video.',
        ERROR_MESSAGE = [
            'An error occurred. ',
            'Please refresh the page and try viewing the video again.'
        ].join(''),
        state;

    beforeEach(function () {
        loadFixtures('video.html');
        state = {
            el: $('.video'),
            progressElement: $('.problem-progress'),
            statusElement: $('.problem-feedback'),
            videoPlayer: {
                duration: jasmine.createSpy().andReturn(100)
            },
            storage: {
                setItem: jasmine.createSpy(),
                getItem: jasmine.createSpy(),
            },
            config: {
                hasScore: true,
                startTime: 0,
                endTime: null,
                maxScore: '1.0',
                score: null,
                gradeUrl: '/grade_url',
                graders: {
                    scored_on_end: {
                        isScored: false,
                        graderValue: true,
                        saveState: false
                    },
                    scored_on_percent: {
                        isScored: false,
                        graderValue: 2,
                        saveState: true
                    }
                }
            },
            isFlashMode: jasmine.createSpy().andReturn(false)
        };
    });

    describe('initialize', function () {
        it('Score is shown if module is graded.', function () {
            state.config.score = '0.5';
            new Grader(state, i18n);
            expect(state.progressElement.text()).toBe(SCORED_TEXT);
        });

        it('Score is hidden if module does not graded.', function () {
            new Grader(state, i18n);
            expect(state.progressElement.text()).toBe(POSSIBLE_SCORES);
        });

        it('Score is hidden if incorrect score was retrieved.', function () {
            state.config.score = 'a0.5a';
            new Grader(state, i18n);
            expect(state.progressElement.text()).toBe(POSSIBLE_SCORES);
        });
    });

    describe('getGraders', function () {
        it('returns collection with graders', function () {
            var getGraders = Grader.prototype.getGraders;

            new Grader(state, i18n);
            expect(getGraders(state.el, state).length).toBe(2);
        });
    });

    describe('Status bar', function () {
        beforeEach(function () {
            state.config.graders.scored_on_percent.isScored = true;
            jasmine.Clock.useMock();
        });

        it('shows success message', function () {
            new Grader(state, i18n);

            expect(state.progressElement.text()).toBe(POSSIBLE_SCORES);
            expect($('.problem-feedback').length).toBe(0);

            jasmine.stubRequests();
            state.el.trigger('play');
            jasmine.Clock.tick(10);
            state.el.trigger('ended');

            expect(state.progressElement.text()).toBe(SCORED_TEXT);
            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            expect(state.storage.setItem).toHaveBeenCalledWith(
                'score', '0.5', true
            );
        });

        it('shows error message', function () {
            runs(function () {
                new Grader(state, i18n);

                expect(state.progressElement.text()).toBe(POSSIBLE_SCORES);
                expect($('.problem-feedback').length).toBe(0);

                state.el.trigger('play');
                jasmine.Clock.tick(10);
                state.el.trigger('ended');
            });

            waitsFor(function () {
                return $('.problem-feedback').length;
            }, 'Respond from server does not received.', WAIT_TIMEOUT);

            runs(function () {
                expect(state.progressElement.text()).toBe(POSSIBLE_SCORES);
                expect($('.problem-feedback').text()).toBe(ERROR_MESSAGE);
                expect(state.storage.setItem).not.toHaveBeenCalled();
            });
        });
    });

    describe('BasicGrader', function () {
        beforeEach(function () {
            state.config.graders['basic_grader'] = {
                isScored: false,
                graderValue: true,
                saveState: false
            };
            state.config.graders.scored_on_percent.isScored = true;
            state.config.graders.scored_on_end.isScored = true;
            jasmine.stubRequests();
            new Grader(state, i18n);
        });

        it('updates status message when done on play', function () {
            state.el.trigger('play');
            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
        });

        it('updates status message when done on video download', function () {
            state.el.find('.video-download-button').trigger('click');
            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
        });
    });

    describe('GradeOnEnd', function () {
        beforeEach(function () {
            jasmine.Clock.useMock();
            state.config.graders.scored_on_percent.isScored = true;
            jasmine.stubRequests();
        });

        it('updates status message when done on video download', function () {
            new Grader(state, i18n);
            state.el.find('.video-download-button').trigger('click');
            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
        });

        describe('ended', function () {
            beforeEach(function () {
                new Grader(state, i18n);
            });

            it('updates status message when done', function () {
                state.el.trigger('play');
                jasmine.Clock.tick(10);
                state.el.trigger('ended');
                expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            });

            it('updates just once', function () {
                state.el.trigger('play');
                jasmine.Clock.tick(10);
                state.el.trigger('ended');
                state.el.trigger('ended');
                state.el.trigger('ended');
                expect(state.storage.setItem.calls.length).toBe(1);
            });

            it('updates status message when seek to the end', function () {
                state.el.trigger('play');
                jasmine.Clock.tick(2);
                state.el.trigger('seek', [100]);
                jasmine.Clock.tick(10);
                expect(state.storage.setItem.calls.length).toBe(1);
            });
        });

        describe('endTime', function () {
            beforeEach(function () {
                state.config.startTime = 10;
                state.config.endTime = 20;
                new Grader(state, i18n);
            });

            it('updates status message when done', function () {
                state.el.trigger('play');
                jasmine.Clock.tick(10);
                state.el.trigger('endTime');
                expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            });

            it('updates just once', function () {
                state.el.trigger('play');
                jasmine.Clock.tick(10);
                state.el.trigger('endTime');
                state.el.trigger('endTime');
                state.el.trigger('endTime');
                expect(state.storage.setItem.calls.length).toBe(1);
            });

            it('updates status message when seek to the end', function () {
                state.el.trigger('play');
                jasmine.Clock.tick(2);
                state.el.trigger('seek', [20.5]);
                jasmine.Clock.tick(10);
                expect(state.storage.setItem.calls.length).toBe(1);
            });
        });
    });

    describe('GradeOnPercent', function () {
        beforeEach(function () {
            state.config.graders.scored_on_end.isScored = true;
            jasmine.stubRequests();
            spyOn(_, 'throttle').andCallFake(function(f){ return f; }) ;
            jasmine.Clock.useMock();
            this.addMatchers({
                assertState: function (expected) {
                    var actual = this.actual.getStates();
                    return this.env.equals_(actual, expected);
                }
            });
        });

        var createStateList = function (len, val) {
            return $.map(_.range(len), function () {
                return val;
            });
        }

        it('shows success message', function () {
            new Grader(state, i18n);
            state.el.trigger('play');
            jasmine.Clock.tick(10);
            expect($('.problem-feedback').length).toBe(0);
            state.el.trigger('progress', [0.9]);
            expect($('.problem-feedback').length).toBe(0);
            state.el.trigger('progress', [1.1]);
            expect($('.problem-feedback').length).toBe(0);
            state.el.trigger('progress', [1.5]);
            expect($('.problem-feedback').length).toBe(0);
            state.el.trigger('progress', [2.1]);
            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            expect(state.videoGrader).assertState({
                'scored_on_percent': createStateList(3, 1)
            });
        });

        it('shows success message if percent equal 100', function () {
            state.config.graders.scored_on_percent.graderValue = 100;
            new Grader(state, i18n);
            state.el.trigger('play');
            jasmine.Clock.tick(10);

            $.each(_.range(202), function(index, val) {
                state.el.trigger('progress', [0.5 * index]);
            });

            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            expect(state.videoGrader).assertState({
                'scored_on_percent': createStateList(101, 1)
            });
        });

        it('shows success message immediately if percent equal 0', function () {
            state.config.graders.scored_on_percent.graderValue = 0;
            new Grader(state, i18n);
            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            expect(state.videoGrader).assertState({
                'scored_on_percent': []
            });
        });

        it('shows success message if duration is less than 20s', function () {
            state.videoPlayer.duration.andReturn(1);
            state.config.graders.scored_on_percent.graderValue = 50;
            new Grader(state, i18n);
            state.el.trigger('play');
            jasmine.Clock.tick(10);

            for (var i = 0, k = 0; i <= 5; i++, k += 0.2) {
                state.el.trigger('progress', [k]);
            }

            expect($('.problem-feedback').text()).toBe(SUCCESS_MESSAGE);
            expect(state.videoGrader).assertState({
                'scored_on_percent': createStateList(3, 1)
            });
        });

    });

    describe('getStartEndTimes', function () {
        var config = {
                'scored_on_end': {
                    isScored: false
                }
            }, grader;

        beforeEach(function () {
            spyOn(AbstractGrader.prototype, 'getGrader');
            spyOn(AbstractGrader.prototype, 'sendGradeOnSuccess');
        });

        describe('startTime', function () {
            it('returns initial value', function () {
                var actual;

                state.config.startTime = 10;
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes();
                expect(actual).toEqual({
                    start: 10,
                    end: 100,
                    size: 90,
                    duration: 100
                });
            });

            it('returns 0 if it is bigger than duration', function () {
                var actual;

                state.config.startTime = 100;
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes();
                expect(actual).toEqual({
                    start: 0,
                    end: 100,
                    size: 100,
                    duration: 100
                });
            });

            it('returns correct values in flash mode', function () {
                var actual;

                state.config.startTime = 10;
                state.speed = 2;
                state.isFlashMode.andReturn(true);
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes();
                expect(actual).toEqual({
                    start: 5,
                    end: 50,
                    size: 45,
                    duration: 100
                });
            });
        });

        describe('endTime', function () {
            it('returns initial value', function () {
                var actual;

                state.config.endTime = 20;
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes();
                expect(actual).toEqual({
                    start: 0,
                    end: 20,
                    size: 20,
                    duration: 100
                });
            });

            it('returns duration if it is bigger than duration', function () {
                var actual;

                state.config.endTime = 100;
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes();
                expect(actual).toEqual({
                    start: 0,
                    end: 100,
                    size: 100,
                    duration: 100
                });
            });

            it('returns duration if it is less than start time', function () {
                var actual;

                state.config.startTime = 50;
                state.config.endTime = 40;
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes();
                expect(actual).toEqual({
                    start: 50,
                    end: 100,
                    size: 50,
                    duration: 100
                });
            });

            it('returns correct values in flash mode', function () {
                var actual;

                state.config.endTime = 10;
                state.speed = 2;
                state.isFlashMode.andReturn(true);
                this.grader = new AbstractGrader(state.el, state, config);
                actual = this.grader.getStartEndTimes()

                expect(actual).toEqual({
                    start: 0,
                    end: 5,
                    size: 5,
                    duration: 100
                });
            });
        });
    });
});
});
}(RequireJS.require));
