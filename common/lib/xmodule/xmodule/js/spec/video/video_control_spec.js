(function (undefined) {
    describe('VideoControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
        });

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            it('render the video controls', function () {
                expect($('.video-controls')).toContain(
                    [
                        '.slider',
                        'ul.vcr',
                        'a.play',
                        '.vidtime',
                        '.add-fullscreen'
                    ].join(',')
                );

                expect($('.video-controls').find('.vidtime'))
                    .toHaveText('0:00 / 0:00');
            });

            it('add ARIA attributes to time control', function () {
                var timeControl = $('div.slider>a');

                expect(timeControl).toHaveAttrs({
                    'role': 'slider',
                    'title': 'Video position',
                    'aria-disabled': 'false'
                });

                expect(timeControl).toHaveAttr('aria-valuetext');
            });

            it('add ARIA attributes to play control', function () {
                var playControl = $('ul.vcr a');

                expect(playControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Play',
                    'aria-disabled': 'false'
                });
            });

            it('add ARIA attributes to fullscreen control', function () {
                var fullScreenControl = $('a.add-fullscreen');

                expect(fullScreenControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Fill browser',
                    'aria-disabled': 'false'
                });
            });

            it('bind the playback button', function () {
                expect($('.video_control')).toHandleWith(
                    'click',
                    state.videoControl.togglePlayback
                );
            });

            describe('when on a non-touch based device', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                });

                it('add the play class to video control', function () {
                    expect($('.video_control')).toHaveClass('play');
                    expect($('.video_control')).toHaveAttr(
                        'title', 'Play'
                    );
                });
            });

            describe('when on a touch based device', function () {
                beforeEach(function () {
                    window.onTouchBasedDevice.andReturn(['iPad']);
                    state = jasmine.initializePlayer();
                });

                it(
                    'does not add the play class to video control',
                    function ()
                {
                    expect($('.video_control')).toHaveClass('play');
                    expect($('.video_control')).toHaveAttr(
                        'title', 'Play'
                    );
                });
            });
        });

        describe('play', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                state.videoControl.play();
            });

            it('switch playback button to play state', function () {
                expect($('.video_control')).not.toHaveClass('play');
                expect($('.video_control')).toHaveClass('pause');
                expect($('.video_control')).toHaveAttr('title', 'Pause');
            });
        });

        describe('pause', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                state.videoControl.pause();
            });

            it('switch playback button to pause state', function () {
                expect($('.video_control')).not.toHaveClass('pause');
                expect($('.video_control')).toHaveClass('play');
                expect($('.video_control')).toHaveAttr('title', 'Play');
            });
        });

        describe('togglePlayback', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            describe(
                'when the control does not have play or pause class',
                function ()
            {
                beforeEach(function () {
                    $('.video_control').removeClass('play')
                        .removeClass('pause');
                });

                describe('when the video is playing', function () {
                    beforeEach(function () {
                        $('.video_control').addClass('play');
                        spyOnEvent(state.videoControl, 'pause');
                        state.videoControl.togglePlayback(jQuery.Event('click'));
                    });

                    it('does not trigger the pause event', function () {
                        expect('pause').not
                            .toHaveBeenTriggeredOn(state.videoControl);
                    });
                });

                describe('when the video is paused', function () {
                    beforeEach(function () {
                        $('.video_control').addClass('pause');
                        spyOnEvent(state.videoControl, 'play');
                        state.videoControl.togglePlayback(jQuery.Event('click'));
                    });

                    it('does not trigger the play event', function () {
                        expect('play').not
                            .toHaveBeenTriggeredOn(state.videoControl);
                    });
                });
            });
        });

        describe('Play placeholder', function () {
            var cases = [
                {
                    name: 'PC',
                    isShown: false,
                    isTouch: null
                }, {
                    name: 'iPad',
                    isShown: true,
                    isTouch: ['iPad']
                }, {
                    name: 'Android',
                    isShown: true,
                    isTouch: ['Android']
                }, {
                    name: 'iPhone',
                    isShown: false,
                    isTouch: ['iPhone']
                }
            ];

            beforeEach(function () {
                jasmine.stubRequests();

                spyOn(window.YT, 'Player').andCallThrough();
            });

            it ('works correctly on calling proper methods', function () {
                var btnPlay;

                state = jasmine.initializePlayer();
                btnPlay = state.el.find('.btn-play');

                state.videoControl.showPlayPlaceholder();

                expect(btnPlay).not.toHaveClass('is-hidden');
                expect(btnPlay).toHaveAttrs({
                    'aria-hidden': 'false',
                    'tabindex': 0
                });

                state.videoControl.hidePlayPlaceholder();

                expect(btnPlay).toHaveClass('is-hidden');
                expect(btnPlay).toHaveAttrs({
                    'aria-hidden': 'true',
                    'tabindex': -1
                });
            });

            $.each(cases, function (index, data) {
                var message = [
                    (data.isShown) ? 'is' : 'is not',
                    ' shown on',
                    data.name
                ].join('');

                it(message, function () {
                    var btnPlay;

                    window.onTouchBasedDevice.andReturn(data.isTouch);
                    state = jasmine.initializePlayer();
                    btnPlay = state.el.find('.btn-play');

                    if (data.isShown) {
                        expect(btnPlay).not.toHaveClass('is-hidden');
                    } else {
                        expect(btnPlay).toHaveClass('is-hidden');
                    }
                });
            });

            $.each(['iPad', 'Android'], function (index, device) {
                it(
                    'is shown on paused video on ' + device +
                    ' in HTML5 player',
                    function ()
                {
                    var btnPlay;

                    window.onTouchBasedDevice.andReturn([device]);
                    state = jasmine.initializePlayer();
                    btnPlay = state.el.find('.btn-play');

                    state.videoControl.play();
                    state.videoControl.pause();

                    expect(btnPlay).not.toHaveClass('is-hidden');
                });

                it(
                    'is hidden on playing video on ' + device +
                    ' in HTML5 player',
                    function ()
                {
                    var btnPlay;

                    window.onTouchBasedDevice.andReturn([device]);
                    state = jasmine.initializePlayer();
                    btnPlay = state.el.find('.btn-play');

                    state.videoControl.play();

                    expect(btnPlay).toHaveClass('is-hidden');
                });

                it(
                    'is hidden on paused video on ' + device +
                    ' in YouTube player',
                    function ()
                {
                    var btnPlay;

                    window.onTouchBasedDevice.andReturn([device]);
                    state = jasmine.initializePlayerYouTube();
                    btnPlay = state.el.find('.btn-play');

                    state.videoControl.play();
                    state.videoControl.pause();

                    expect(btnPlay).toHaveClass('is-hidden');
                });
            });
        });

        it('show', function () {
            var controls;

            state = jasmine.initializePlayer();
            controls = state.el.find('.video-controls');
            controls.addClass('is-hidden');

            state.videoControl.show();
            expect(controls).not.toHaveClass('is-hidden');
        });
    });
}).call(this);
