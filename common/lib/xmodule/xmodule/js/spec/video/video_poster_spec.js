(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoPoster', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
            state = jasmine.initializePlayer();
            spyOn(this.state.videoCommands, 'execute');
        });

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            window.Video.previousState = null;
            window.onTouchBasedDevice = oldOTBD;
        });

        it('do not render itself if poster unavailable', function () {
            expect().toBe();
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
            expect().toBe();
        });

        it('can destroy itself', function () {
            expect().toBe();
        });

    });
}).call(this, window.WAIT_TIMEOUT);
