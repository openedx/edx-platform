(function (undefined) {
    describe('VideoVolumeControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            beforeEach(function () {
                spyOn($.fn, 'slider').andCallThrough();
                state = jasmine.initializePlayer();
            });

            it('initialize currentVolume to 100%', function () {
                // Please note that:
                //     0%   -> 0
                //     100% -> 1.0
                expect(state.videoVolumeControl.currentVolume).toEqual(1);
            });

            it('render the volume control', function () {
                expect(state.videoControl.secondaryControlsEl.html())
                    .toContain("<div class=\"volume\">\n");
            });

            it('create the slider', function () {
                expect($.fn.slider).toHaveBeenCalledWith({
                    orientation: "vertical",
                    range: "min",
                    min: 0,
                    max: 100,
                    value: state.videoVolumeControl.currentVolume,
                    change: state.videoVolumeControl.onChange,
                    slide: state.videoVolumeControl.onChange
                });
            });

            it('add ARIA attributes to slider handle', function () {
                var sliderHandle = $('div.volume-slider>a.ui-slider-handle'),
                    arr = [
                        'muted', 'very low', 'low', 'average', 'loud',
                        'very loud', 'maximum'
                    ];

                expect(sliderHandle).toHaveAttrs({
                    'role': 'slider',
                    'title': 'volume',
                    'aria-disabled': 'false',
                    'aria-valuemin': '0',
                    'aria-valuemax': '100'
                });
                expect(sliderHandle.attr('aria-valuenow')).toBeInRange(0, 100);
                expect(sliderHandle.attr('aria-valuetext')).toBeInArray(arr);
            });

            it('add ARIA attributes to volume control', function () {
                var volumeControl = $('div.volume>a');

                expect(volumeControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Volume',
                    'aria-disabled': 'false'
                });
            });

            it('bind the volume control', function () {
                expect($('.volume>a')).toHandleWith(
                    'click', state.videoVolumeControl.toggleMute
                );
                expect($('.volume')).not.toHaveClass('open');

                $('.volume').mouseenter();
                expect($('.volume')).toHaveClass('open');

                $('.volume').mouseleave();
                expect($('.volume')).not.toHaveClass('open');
            });
        });

        describe('onChange', function () {
            var initialData = [{
                range: 'muted',
                value: 0,
                expectation: 'muted'
            }, {
                range: 'in ]0,20]',
                value: 10,
                expectation: 'very low'
            }, {
                range: 'in ]20,40]',
                value: 30,
                expectation: 'low'
            }, {
                range: 'in ]40,60]',
                value: 50,
                expectation: 'average'
            }, {
                range: 'in ]60,80]',
                value: 70,
                expectation: 'loud'
            }, {
                range: 'in ]80,100[',
                value: 90,
                expectation: 'very loud'
            }, {
                range: 'maximum',
                value: 100,
                expectation: 'maximum'
            }];

            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            describe('when the new volume is more than 0', function () {
                beforeEach(function () {
                    state.videoVolumeControl.onChange(void 0, {
                        value: 60
                    });
                });

                it('set the player volume', function () {
                    expect(state.videoVolumeControl.currentVolume).toEqual(60);
                });

                it('remote muted class', function () {
                    expect($('.volume')).not.toHaveClass('muted');
                });
            });

            describe('when the new volume is 0', function () {
                beforeEach(function () {
                    state.videoVolumeControl.onChange(void 0, {
                        value: 0
                    });
                });

                it('set the player volume', function () {
                    expect(state.videoVolumeControl.currentVolume).toEqual(0);
                });

                it('add muted class', function () {
                    expect($('.volume')).toHaveClass('muted');
                });
            });

            $.each(initialData, function (index, data) {
                describe('when the new volume is ' + data.range, function () {
                    beforeEach(function () {
                        state.videoVolumeControl.onChange(void 0, {
                            value: data.value
                        });
                    });

                    it('changes ARIA attributes', function () {
                        var sliderHandle = $(
                            'div.volume-slider>a.ui-slider-handle'
                        );

                        expect(sliderHandle).toHaveAttrs({
                            'aria-valuenow': data.value.toString(10),
                            'aria-valuetext': data.expectation
                        });
                    });
                });
            });
        });

        describe('toggleMute', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            describe('when the current volume is more than 0', function () {
                beforeEach(function () {
                    state.videoVolumeControl.currentVolume = 60;
                    state.videoVolumeControl.buttonEl.trigger('click');
                });

                it('save the previous volume', function () {
                    expect(state.videoVolumeControl.previousVolume).toEqual(60);
                });

                it('set the player volume', function () {
                    expect(state.videoVolumeControl.currentVolume).toEqual(0);
                });
            });

            describe('when the current volume is 0', function () {
                beforeEach(function () {
                    state.videoVolumeControl.currentVolume = 0;
                    state.videoVolumeControl.previousVolume = 60;
                    state.videoVolumeControl.buttonEl.trigger('click');
                });

                it('set the player volume to previous volume', function () {
                    expect(state.videoVolumeControl.currentVolume).toEqual(60);
                });
            });
        });
    });
}).call(this);
