(function (undefined) {
    describe('VideoProgressSlider', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            state.storage.clear();
        });

        describe('constructor', function () {
            describe('on a non-touch based device', function () {
                beforeEach(function () {
                    spyOn($.fn, 'slider').andCallThrough();

                    state = jasmine.initializePlayer();
                });

                it('build the slider', function () {
                    expect(state.videoProgressSlider.slider).toBe('.slider');
                    expect($.fn.slider).toHaveBeenCalledWith({
                        range: 'min',
                        min: 0,
                        max: null,
                        change: state.videoProgressSlider.onChange,
                        slide: state.videoProgressSlider.onSlide,
                        stop: state.videoProgressSlider.onStop
                    });
                });

                it('build the seek handle', function () {
                    expect(state.videoProgressSlider.handle)
                        .toBe('.slider .ui-slider-handle');
                });
            });

            describe('on a touch-based device', function () {
                it('does not build the slider on iPhone', function () {

                    window.onTouchBasedDevice.andReturn(['iPhone']);

                    state = jasmine.initializePlayer();

                    expect(state.videoProgressSlider).toBeUndefined();

                    // We can't expect $.fn.slider not to have been called,
                    // because sliders are used in other parts of Video.
                });
                $.each(['iPad', 'Android'], function (index, device) {
                    it('build the slider on ' + device, function () {
                        window.onTouchBasedDevice.andReturn([device]);

                        state = jasmine.initializePlayer();

                        expect(state.videoProgressSlider.slider).toBeDefined();
                    });
                });
            });
        });

        describe('play', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            describe('when the slider was already built', function () {
                var spy;

                beforeEach(function () {
                    spy = spyOn(state.videoProgressSlider, 'buildSlider');
                    spy.andCallThrough();
                    state.videoPlayer.play();
                });

                it('does not build the slider', function () {
                    expect(spy.callCount).toEqual(0);
                });
            });

            // Currently, the slider is not rebuilt if it does not exist.
        });

        describe('updatePlayTime', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            describe('when frozen', function () {
                beforeEach(function () {
                    spyOn($.fn, 'slider').andCallThrough();
                    state.videoProgressSlider.frozen = true;
                    state.videoProgressSlider.updatePlayTime(20, 120);
                });

                it('does not update the slider', function () {
                    expect($.fn.slider).not.toHaveBeenCalled();
                });
            });

            describe('when not frozen', function () {
                beforeEach(function () {
                    spyOn($.fn, 'slider').andCallThrough();
                    state.videoProgressSlider.frozen = false;
                    state.videoProgressSlider.updatePlayTime({
                        time: 20,
                        duration: 120
                    });
                });

                it('update the max value of the slider', function () {
                    expect($.fn.slider).toHaveBeenCalledWith(
                        'option', 'max', 120
                    );
                });

                it('update current value of the slider', function () {
                    expect($.fn.slider).toHaveBeenCalledWith(
                        'option', 'value', 20
                    );
                });

                it('required aria values updated', function () {
                    expect(state.videoProgressSlider.handle.attr('aria-valuenow')).toBe('20');
                    expect(state.videoProgressSlider.handle.attr('aria-valuemax')).toBe('120');
                });
            });
        });

        describe('onSlide', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                spyOn($.fn, 'slider').andCallThrough();
                spyOn(state.videoPlayer, 'onSlideSeek').andCallThrough();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('freeze the slider', function () {
                state.videoProgressSlider.onSlide(
                    jQuery.Event('slide'), { value: 20 }
                );

                expect(state.videoProgressSlider.frozen).toBeTruthy();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('trigger seek event', function () {
                state.videoProgressSlider.onSlide(
                    jQuery.Event('slide'), { value: 20 }
                );

                expect(state.videoPlayer.onSlideSeek).toHaveBeenCalled();
            });
        });

        describe('onStop', function () {

            beforeEach(function () {
                jasmine.Clock.useMock();

                state = jasmine.initializePlayer();

                spyOn(state.videoPlayer, 'onSlideSeek').andCallThrough();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('freeze the slider', function () {
                state.videoProgressSlider.onStop(
                    jQuery.Event('stop'), { value: 20 }
                );

                expect(state.videoProgressSlider.frozen).toBeTruthy();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('trigger seek event', function () {
                state.videoProgressSlider.onStop(
                    jQuery.Event('stop'), { value: 20 }
                );

                expect(state.videoPlayer.onSlideSeek).toHaveBeenCalled();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('set timeout to unfreeze the slider', function () {
                state.videoProgressSlider.onStop(
                    jQuery.Event('stop'), { value: 20 }
                );

                jasmine.Clock.tick(200);

                expect(state.videoProgressSlider.frozen).toBeFalsy();
            });
        });

        it('getRangeParams' , function () {
            var testCases = [
                    {
                        startTime: 10,
                        endTime: 20,
                        duration: 150
                    },
                    {
                        startTime: 90,
                        endTime: 100,
                        duration: 100
                    },
                    {
                        startTime: 0,
                        endTime: 200,
                        duration: 200
                    }
                ];

            state = jasmine.initializePlayer();

            $.each(testCases, function (index, testCase) {
                var step = 100/testCase.duration,
                    left = testCase.startTime*step,
                    width = testCase.endTime*step - left,
                    expectedParams = {
                        left: left + '%',
                        width: width + '%'
                    },
                    params = state.videoProgressSlider.getRangeParams(
                        testCase.startTime, testCase.endTime, testCase.duration
                    );

                expect(params).toEqual(expectedParams);
            });
        });

        describe('notifyThroughHandleEnd', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                spyOnEvent(state.videoProgressSlider.handle, 'focus');
                spyOn(state.videoProgressSlider, 'notifyThroughHandleEnd')
                    .andCallThrough();
            });

            it('params.end = true', function () {
                state.videoProgressSlider.notifyThroughHandleEnd({end: true});

                expect(state.videoProgressSlider.handle.attr('title'))
                    .toBe('Video ended');

                expect('focus').toHaveBeenTriggeredOn(
                    state.videoProgressSlider.handle
                );
            });

            it('params.end = false', function () {
                state.videoProgressSlider.notifyThroughHandleEnd({end: false});

                expect(state.videoProgressSlider.handle.attr('title'))
                    .toBe('Video position');

                expect('focus').not.toHaveBeenTriggeredOn(
                    state.videoProgressSlider.handle
                );
            });

            it('is called when video plays', function () {
                state.videoPlayer.play();

                waitsFor(function () {
                    return state.videoPlayer.isPlaying();
                }, 'duration is set, video is playing', 5000);

                runs(function () {
                    expect(state.videoProgressSlider.notifyThroughHandleEnd)
                        .toHaveBeenCalledWith({end: false});
                });
            });
        });

        it('getTimeDescription', function () {
            var cases = {
                    '0': '0 seconds',
                    '1': '1 second',
                    '10': '10 seconds',

                    '60': '1 minute 0 seconds',
                    '121': '2 minutes 1 second',

                    '3670': '1 hour 1 minute 10 seconds',
                    '21541': '5 hours 59 minutes 1 second',
                },
                getTimeDescription;

            state = jasmine.initializePlayer();

            getTimeDescription = state.videoProgressSlider.getTimeDescription;

            $.each(cases, function(input, output) {
                expect(getTimeDescription(input)).toBe(output);
            });
        });

    });

}).call(this);
