(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoSkipControl', function () {
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

        it('can render the control when video starts playing', function () {
            expect($('.skip-control')).not.toExist();
            state.el.trigger('play');
            expect($('.skip-control')).toExist();
        });

        it('add ARIA attributes to play control', function () {
            expect($('.skip-control')).toHaveAttrs({
                'role': 'button',
                'title': 'Do not show again',
                'aria-disabled': 'false'
            });
        });

        it('can skip the video on click', function () {
            $('.skip-control').click();
            expect(state.videoCommands.execute).toHaveBeenCalledWith('skip', true);
        });

        it('can destroy itself', function () {
            expect().toBe();
        });

    });
}).call(this, window.WAIT_TIMEOUT);
