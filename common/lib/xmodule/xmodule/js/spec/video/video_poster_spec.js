(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoPoster', function () {
        var state, oldOTBD;

        describe('VideoWithPoster', function () {

            beforeEach(function () {
                oldOTBD = window.onTouchBasedDevice;
                window.onTouchBasedDevice = jasmine
                    .createSpy('onTouchBasedDevice').andReturn(null);
                state = jasmine.initializePlayer('video_with_bumper.html');
                spyOn(state.bumperState.videoBumper, 'play');
            });

            afterEach(function () {
                $('source').remove();
                state.storage.clear();
                window.Video.previousState = null;
                window.onTouchBasedDevice = oldOTBD;
            });

            it('can render the poster', function () {
                expect($('.poster')).toExist();
                expect($('.btn-play')).toExist();
            });

            it('destroy itself on "play" event', function () {
                state.el.trigger('play');
                expect($('.poster')).not.toExist();
            });

            it('destroy itself on "destroy" event', function () {
                state.el.trigger('destroy');
                expect($('.poster')).not.toExist();
            });

            it('can call the callback on click', function () {
                $('.btn-play').click();
                expect(state.bumperState.videoBumper.play).toHaveBeenCalled();
            });

        });

        describe('VideoWithoutPoster', function () {

            beforeEach(function () {
                oldOTBD = window.onTouchBasedDevice;
                window.onTouchBasedDevice = jasmine
                    .createSpy('onTouchBasedDevice').andReturn(null);
                state = jasmine.initializePlayer();
            });

            afterEach(function () {
                $('source').remove();
                state.storage.clear();
                window.Video.previousState = null;
                window.onTouchBasedDevice = oldOTBD;
            });

            it('do not render itself if poster unavailable', function () {
                expect($('.poster')).not.toExist();
            });
        });

    });
}).call(this, window.WAIT_TIMEOUT);
