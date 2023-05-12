/* eslint-disable-next-line no-shadow-restricted-names, no-unused-vars */
(function(undefined) {
    describe('VideoProgressSlider', function() {
        // eslint-disable-next-line no-var
        var state, oldOTBD;

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            // eslint-disable-next-line no-undef
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .and.returnValue(null);
        });

        afterEach(function() {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            state.storage.clear();
            state.videoPlayer.destroy();
        });

        describe('constructor', function() {
            describe('on a non-touch based device', function() {
                beforeEach(function() {
                    // eslint-disable-next-line no-undef
                    spyOn($.fn, 'slider').and.callThrough();

                    // eslint-disable-next-line no-undef
                    state = jasmine.initializePlayer();
                });

                it('build the slider', function() {
                    expect($('.slider').toArray()).toContain(state.videoProgressSlider.slider);
                    expect($.fn.slider).toHaveBeenCalledWith({
                        range: 'min',
                        min: 0,
                        max: null,
                        slide: state.videoProgressSlider.onSlide,
                        stop: state.videoProgressSlider.onStop,
                        step: 5
                    });
                });

                it('build the seek handle', function() {
                    expect($('.ui-slider-handle').toArray())
                        .toContain(state.videoProgressSlider.handle);
                });

                it('add ARIA attributes to time control', function() {
                    // eslint-disable-next-line no-var
                    var $timeControl = $('div.slider > .progress-handle');

                    expect($timeControl).toHaveAttrs({
                        role: 'slider',
                        'aria-label': 'Video position. Press space to toggle playback',
                        'aria-disabled': 'false'
                    });

                    expect($timeControl).toHaveAttr('aria-valuetext');
                });
            });

            describe('on a touch-based device', function() {
                it('does not build the slider on iPhone', function() {
                    window.onTouchBasedDevice.and.returnValue(['iPhone']);

                    // eslint-disable-next-line no-undef
                    state = jasmine.initializePlayer();

                    expect(state.videoProgressSlider).toBeUndefined();

                    // We can't expect $.fn.slider not to have been called,
                    // because sliders are used in other parts of Video.
                });
                $.each(['iPad', 'Android'], function(index, device) {
                    it('build the slider on ' + device, function() {
                        window.onTouchBasedDevice.and.returnValue([device]);

                        // eslint-disable-next-line no-undef
                        state = jasmine.initializePlayer();

                        expect(state.videoProgressSlider.slider).toBeDefined();
                    });
                });
            });
        });

        describe('play', function() {
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                state = jasmine.initializePlayer();
            });

            describe('when the slider was already built', function() {
                // eslint-disable-next-line no-var
                var spy;

                beforeEach(function() {
                    // eslint-disable-next-line no-undef
                    spy = spyOn(state.videoProgressSlider, 'buildSlider');
                    spy.and.callThrough();
                    state.videoPlayer.play();
                });

                it('does not build the slider', function() {
                    expect(spy.calls.count()).toEqual(0);
                });
            });

            // Currently, the slider is not rebuilt if it does not exist.
        });

        describe('updatePlayTime', function() {
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                state = jasmine.initializePlayer();
            });

            describe('when frozen', function() {
                beforeEach(function() {
                    // eslint-disable-next-line no-undef
                    spyOn($.fn, 'slider').and.callThrough();
                    state.videoProgressSlider.frozen = true;
                    state.videoProgressSlider.updatePlayTime(20, 120);
                });

                it('does not update the slider', function() {
                    expect($.fn.slider).not.toHaveBeenCalled();
                });
            });

            describe('when not frozen', function() {
                beforeEach(function() {
                    // eslint-disable-next-line no-undef
                    spyOn($.fn, 'slider').and.callThrough();
                    state.videoProgressSlider.frozen = false;
                    state.videoProgressSlider.updatePlayTime({
                        time: 20,
                        duration: 120
                    });
                });

                it('update the max value of the slider', function() {
                    expect($.fn.slider).toHaveBeenCalledWith(
                        'option', 'max', 120
                    );
                });

                it('update current value of the slider', function() {
                    expect($.fn.slider).toHaveBeenCalledWith(
                        'option', 'value', 20
                    );
                });

                it('required aria values updated', function() {
                    expect(state.videoProgressSlider.handle.attr('aria-valuenow')).toBe('20');
                    expect(state.videoProgressSlider.handle.attr('aria-valuemax')).toBe('120');
                });
            });
        });

        describe('onSlide', function() {
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                state = jasmine.initializePlayer();

                // eslint-disable-next-line no-undef
                spyOn($.fn, 'slider').and.callThrough();
                // eslint-disable-next-line no-undef
                spyOn(state.videoPlayer, 'onSlideSeek').and.callThrough();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('freeze the slider', function() {
                state.videoProgressSlider.onSlide(
                    // eslint-disable-next-line no-undef
                    jQuery.Event('slide'), {value: 20}
                );

                expect(state.videoProgressSlider.frozen).toBeTruthy();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('trigger seek event', function() {
                state.videoProgressSlider.onSlide(
                    // eslint-disable-next-line no-undef
                    jQuery.Event('slide'), {value: 20}
                );

                expect(state.videoPlayer.onSlideSeek).toHaveBeenCalled();
            });
        });

        describe('onStop', function() {
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                jasmine.clock().install();

                // eslint-disable-next-line no-undef
                state = jasmine.initializePlayer();

                // eslint-disable-next-line no-undef
                spyOn(state.videoPlayer, 'onSlideSeek').and.callThrough();
            });

            afterEach(function() {
                // eslint-disable-next-line no-undef
                jasmine.clock().uninstall();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('freeze the slider', function() {
                state.videoProgressSlider.onStop(
                    // eslint-disable-next-line no-undef
                    jQuery.Event('stop'), {value: 20}
                );

                expect(state.videoProgressSlider.frozen).toBeTruthy();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('trigger seek event', function() {
                state.videoProgressSlider.onStop(
                    // eslint-disable-next-line no-undef
                    jQuery.Event('stop'), {value: 20}
                );

                expect(state.videoPlayer.onSlideSeek).toHaveBeenCalled();
            });

            // Disabled 12/30/13 due to flakiness in master
            xit('set timeout to unfreeze the slider', function() {
                state.videoProgressSlider.onStop(
                    // eslint-disable-next-line no-undef
                    jQuery.Event('stop'), {value: 20}
                );

                // eslint-disable-next-line no-undef
                jasmine.clock().tick(200);

                expect(state.videoProgressSlider.frozen).toBeFalsy();
            });
        });

        it('getRangeParams', function() {
            // eslint-disable-next-line no-var
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

            // eslint-disable-next-line no-undef
            state = jasmine.initializePlayer();

            $.each(testCases, function(index, testCase) {
                // eslint-disable-next-line no-var
                var step = 100 / testCase.duration,
                    left = testCase.startTime * step,
                    width = testCase.endTime * step - left,
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

        describe('notifyThroughHandleEnd', function() {
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                state = jasmine.initializePlayer();

                spyOnEvent(state.videoProgressSlider.handle, 'focus');
                // eslint-disable-next-line no-undef
                spyOn(state.videoProgressSlider, 'notifyThroughHandleEnd')
                    .and.callThrough();
            });

            it('params.end = true', function() {
                state.videoProgressSlider.notifyThroughHandleEnd({end: true});

                expect(state.videoProgressSlider.handle.attr('title'))
                    .toBe('Video ended');

                expect('focus').toHaveBeenTriggeredOn(
                    state.videoProgressSlider.handle
                );
            });

            it('params.end = false', function() {
                state.videoProgressSlider.notifyThroughHandleEnd({end: false});

                expect(state.videoProgressSlider.handle.attr('title'))
                    .toBe('Video position');

                expect('focus').not.toHaveBeenTriggeredOn(
                    state.videoProgressSlider.handle
                );
            });

            it('is called when video plays', function(done) {
                state.videoPlayer.play();
                // eslint-disable-next-line no-undef
                jasmine.waitUntil(function() {
                    return state.videoPlayer.isPlaying();
                }).done(function() {
                    expect(state.videoProgressSlider.notifyThroughHandleEnd).toHaveBeenCalledWith({end: false});
                }).always(done);
            });
        });

        it('getTimeDescription', function() {
            // eslint-disable-next-line no-var
            var cases = {
                    0: '0 seconds',
                    1: '1 second',
                    10: '10 seconds',

                    60: '1 minute 0 seconds',
                    121: '2 minutes 1 second',

                    3670: '1 hour 1 minute 10 seconds',
                    21541: '5 hours 59 minutes 1 second'
                },
                getTimeDescription;

            // eslint-disable-next-line no-undef
            state = jasmine.initializePlayer();

            getTimeDescription = state.videoProgressSlider.getTimeDescription;

            $.each(cases, function(input, output) {
                expect(getTimeDescription(input)).toBe(output);
            });
        });

        it('can destroy itself', function() {
            // eslint-disable-next-line no-undef
            state = jasmine.initializePlayer();
            state.videoProgressSlider.destroy();
            expect(state.videoProgressSlider).toBeUndefined();
            expect($('.slider')).toBeEmpty();
        });
    });
}).call(this);
