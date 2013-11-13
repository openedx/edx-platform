(function() {
    describe('VideoProgressSlider', function() {
        var state, videoPlayer, videoProgressSlider, oldOTBD;

        function initialize() {
            loadFixtures('video_all.html');
            state = new Video('#example');
            videoPlayer = state.videoPlayer;
            videoProgressSlider = state.videoProgressSlider;
        }

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(false);
        });

        afterEach(function() {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function() {
            describe('on a non-touch based device', function() {
                beforeEach(function() {
                    spyOn($.fn, 'slider').andCallThrough();
                    initialize();
                });

                it('build the slider', function() {
                    expect(videoProgressSlider.slider).toBe('.slider');
                    expect($.fn.slider).toHaveBeenCalledWith({
                        range: 'min',
                        change: videoProgressSlider.onChange,
                        slide: videoProgressSlider.onSlide,
                        stop: videoProgressSlider.onStop
                    });
                });

                it('build the seek handle', function() {
                    expect(videoProgressSlider.handle)
                        .toBe('.slider .ui-slider-handle');
                });
            });

            describe('on a touch-based device', function() {
                beforeEach(function() {
                    window.onTouchBasedDevice.andReturn(true);
                    spyOn($.fn, 'slider').andCallThrough();
                    initialize();
                });

                it('does not build the slider', function() {
                    expect(videoProgressSlider.slider).toBeUndefined();

                    // We can't expect $.fn.slider not to have been called,
                    // because sliders are used in other parts of Video.
                });
            });
        });

        describe('play', function() {
            beforeEach(function() {
                initialize();
            });

            describe('when the slider was already built', function() {
                var spy;

                beforeEach(function() {
                    spy = spyOn(videoProgressSlider, 'buildSlider');
                    spy.andCallThrough();
                    videoPlayer.play();
                });

                it('does not build the slider', function() {
                    expect(spy.callCount).toEqual(0);
                });
            });

            // Currently, the slider is not rebuilt if it does not exist.
        });

        describe('updatePlayTime', function() {
            beforeEach(function() {
                initialize();
            });

            describe('when frozen', function() {
                beforeEach(function() {
                    spyOn($.fn, 'slider').andCallThrough();
                    videoProgressSlider.frozen = true;
                    videoProgressSlider.updatePlayTime(20, 120);
                });

                it('does not update the slider', function() {
                    expect($.fn.slider).not.toHaveBeenCalled();
                });
            });

            describe('when not frozen', function() {
                beforeEach(function() {
                    spyOn($.fn, 'slider').andCallThrough();
                    videoProgressSlider.frozen = false;
                    videoProgressSlider.updatePlayTime({
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
            });
        });

        describe('onSlide', function() {
            beforeEach(function() {
                initialize();
                spyOn($.fn, 'slider').andCallThrough();
                spyOn(videoPlayer, 'onSlideSeek').andCallThrough();

                state.videoPlayer.play();

                waitsFor(function () {
                    var duration = videoPlayer.duration(),
                        currentTime = videoPlayer.currentTime;

                    return (
                        isFinite(currentTime) &&
                        currentTime > 0 &&
                        isFinite(duration) &&
                        duration > 0
                    );
                }, 'video begins playing', 10000);
            });

            it('freeze the slider', function() {
                runs(function () {
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 20 }
                    );

                    expect(videoProgressSlider.frozen).toBeTruthy();
                });
            });

            // Turned off test due to flakiness (30.10.2013).
            xit('trigger seek event', function() {
                runs(function () {
                    videoProgressSlider.onSlide(
                        jQuery.Event('slide'), { value: 20 }
                    );

                    expect(videoPlayer.onSlideSeek).toHaveBeenCalled();

                    waitsFor(function () {
                        return Math.round(videoPlayer.currentTime) === 20;
                    }, 'currentTime got updated', 10000);
                });
            });
        });

        describe('onStop', function() {
            // We will store default window.setTimeout() function here.
            var oldSetTimeout = null;

            beforeEach(function() {
                // Store original window.setTimeout() function. If we do not do
                // this, then all other tests that rely on code which uses
                // window.setTimeout() function might (and probably will) fail.
                oldSetTimeout = window.setTimeout;
                // Redefine window.setTimeout() function as a spy.
                window.setTimeout = jasmine.createSpy()
                    .andCallFake(function (callback, timeout) {
                        return 5;
                    });
                window.setTimeout.andReturn(100);

                initialize();
                spyOn(videoPlayer, 'onSlideSeek').andCallThrough();
                videoPlayer.play();

                waitsFor(function () {
                    var duration = videoPlayer.duration(),
                        currentTime = videoPlayer.currentTime;

                    return (
                        isFinite(currentTime) &&
                        currentTime > 0 &&
                        isFinite(duration) &&
                        duration > 0
                    );
                }, 'video begins playing', 10000);
            });

            afterEach(function () {
                // Reset the default window.setTimeout() function. If we do not
                // do this, then all other tests that rely on code which uses
                // window.setTimeout() function might (and probably will) fail.
                window.setTimeout = oldSetTimeout;
            });

            it('freeze the slider', function() {
                runs(function () {
                    videoProgressSlider.onStop(
                        jQuery.Event('stop'), { value: 20 }
                    );

                    expect(videoProgressSlider.frozen).toBeTruthy();
                });
            });

            // Turned off test due to flakiness (30.10.2013).
            xit('trigger seek event', function() {
                runs(function () {
                    videoProgressSlider.onStop(
                        jQuery.Event('stop'), { value: 20 }
                    );

                    expect(videoPlayer.onSlideSeek).toHaveBeenCalled();

                    waitsFor(function () {
                        return Math.round(videoPlayer.currentTime) === 20;
                    }, 'currentTime got updated', 10000);
                });
            });

            it('set timeout to unfreeze the slider', function() {
                runs(function () {
                    videoProgressSlider.onStop(
                        jQuery.Event('stop'), { value: 20 }
                    );

                    expect(window.setTimeout).toHaveBeenCalledWith(
                        jasmine.any(Function), 200
                    );
                    window.setTimeout.mostRecentCall.args[0]();
                    expect(videoProgressSlider.frozen).toBeFalsy();
                });
            });
        });

        it('getRangeParams' , function() {
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

            initialize();

            $.each(testCases, function(index, testCase) {
                var step = 100/testCase.duration,
                    left = testCase.startTime*step,
                    width = testCase.endTime*step - left,
                    expectedParams = {
                        left: left + '%',
                        width: width + '%'
                    },
                    params = videoProgressSlider.getRangeParams(
                        testCase.startTime, testCase.endTime, testCase.duration
                    );

                expect(params).toEqual(expectedParams);
            });
        });
    });

}).call(this);
