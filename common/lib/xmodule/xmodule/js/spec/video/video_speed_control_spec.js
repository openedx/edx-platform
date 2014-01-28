(function (undefined) {
    describe('VideoSpeedControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            describe('always', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                });

                it('add the video speed control to player', function () {
                    var li, secondaryControls;

                    secondaryControls = $('.secondary-controls');
                    li = secondaryControls.find('.video_speeds li');

                    expect(secondaryControls).toContain('.speeds');
                    expect(secondaryControls).toContain('.video_speeds');
                    expect(secondaryControls.find('p.active').text())
                        .toBe('1.0x');
                    expect(li.filter('.active')).toHaveData(
                        'speed', state.videoSpeedControl.currentSpeed
                    );
                    expect(li.length).toBe(state.videoSpeedControl.speeds.length);

                    $.each(li.toArray().reverse(), function (index, link) {
                        expect($(link)).toHaveData(
                            'speed', state.videoSpeedControl.speeds[index]
                        );
                        expect($(link).find('a').text()).toBe(
                            state.videoSpeedControl.speeds[index] + 'x'
                        );
                    });
                });

                it('add ARIA attributes to speed control', function () {
                    var speedControl = $('div.speeds>a');

                    expect(speedControl).toHaveAttrs({
                        'role': 'button',
                        'title': 'Speeds',
                        'aria-disabled': 'false'
                    });
                });

                it('bind to change video speed link', function () {
                    expect($('.video_speeds a')).toHandleWith(
                        'click', state.videoSpeedControl.changeVideoSpeed
                    );
                });
            });

            describe('when running on touch based device', function () {
                $.each(['iPad', 'Android'], function (index, device) {
                    it('is not rendered on' + device, function () {
                        window.onTouchBasedDevice.andReturn([device]);
                        state = jasmine.initializePlayer();

                        expect(state.el.find('div.speeds')).not.toExist();
                    });
                });
            });

            describe('when running on non-touch based device', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                });

                it('open the speed toggle on hover', function () {
                    $('.speeds').mouseenter();
                    expect($('.speeds')).toHaveClass('open');

                    $('.speeds').mouseleave();
                    expect($('.speeds')).not.toHaveClass('open');
                });

                it('close the speed toggle on mouse out', function () {
                    $('.speeds').mouseenter().mouseleave();

                    expect($('.speeds')).not.toHaveClass('open');
                });

                it('close the speed toggle on click', function () {
                    $('.speeds').mouseenter().click();

                    expect($('.speeds')).not.toHaveClass('open');
                });

                // Tabbing depends on the following order:
                // 1. Play anchor
                // 2. Speed anchor
                // 3. A number of speed entry anchors
                // 4. Volume anchor
                // If another focusable element is inserted or if the order is
                // changed, things will malfunction as a flag,
                // state.previousFocus, is set in the 1,3,4 elements and is
                // used to determine the behavior of foucus() and blur() for
                // the speed anchor.
                it(
                    'checks for a certain order in focusable elements in ' +
                    'video controls',
                    function ()
                {
                    var foundFirst = false,
                        playIndex, speedIndex, firstSpeedEntry, lastSpeedEntry,
                        volumeIndex;

                    $('.video-controls').find('a, :focusable').each(
                        function (index)
                    {
                        if ($(this).hasClass('video_control')) {
                            playIndex = index;
                        } else if ($(this).parent().hasClass('speeds')) {
                            speedIndex = index;
                        } else if ($(this).hasClass('speed_link')) {
                            if (!foundFirst) {
                                firstSpeedEntry = index;
                                foundFirst = true;
                            }

                            lastSpeedEntry = index;
                        } else if ($(this).parent().hasClass('volume')) {
                            volumeIndex = index;
                        }
                    });

                    expect(playIndex+1).toEqual(speedIndex);
                    expect(speedIndex+1).toEqual(firstSpeedEntry);
                    expect(lastSpeedEntry+1).toEqual(volumeIndex);
                });
            });
        });

        describe('changeVideoSpeed', function () {
            // This is an unnecessary test. The internal browser API, and
            // YouTube API detect (and do not do anything) if there is a
            // request for a speed that is already set.
            //
            //     describe("when new speed is the same") ...

            describe('when new speed is not the same', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoSpeedControl.setSpeed(1.0);
                    spyOn(state.videoPlayer, 'onSpeedChange').andCallThrough();

                    $('li[data-speed="0.75"] a').click();
                });

                it('trigger speedChange event', function () {
                    expect(state.videoPlayer.onSpeedChange).toHaveBeenCalled();
                    expect(state.videoSpeedControl.currentSpeed).toEqual(0.75);
                });
            });

            describe(
                'make sure the speed control gets the focus afterwards',
                function ()
            {
                var anchor;

                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    anchor= $('.speeds > a').first();
                    state.videoSpeedControl.setSpeed(1.0);
                    spyOnEvent(anchor, 'focus');
                });

                it('when the speed is the same', function () {
                    $('li[data-speed="1.0"] a').click();
                    expect('focus').toHaveBeenTriggeredOn(anchor);
                });

                it('when the speed is not the same', function () {
                    $('li[data-speed="0.75"] a').click();
                    expect('focus').toHaveBeenTriggeredOn(anchor);
                });
            });
        });

        describe('onSpeedChange', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                $('li[data-speed="1.0"] a').addClass('active');
                state.videoSpeedControl.setSpeed(0.75);
            });

            it('set the new speed as active', function () {
                expect($('.video_speeds li[data-speed="1.0"]'))
                    .not.toHaveClass('active');
                expect($('.video_speeds li[data-speed="0.75"]'))
                    .toHaveClass('active');
                expect($('.speeds p.active')).toHaveHtml('0.75x');
            });
        });
    });
}).call(this);
