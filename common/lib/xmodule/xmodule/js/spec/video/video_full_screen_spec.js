(function (WAIT_TIMEOUT) {
    'use strict';

    describe('VideoFullScreen', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
        });

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            window.Video.previousState = null;
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            it('render the fullscreen control', function () {
                expect($('.add-fullscreen')).toExist();
            });

            it('add ARIA attributes to fullscreen control', function () {
                var fullScreenControl = $('.add-fullscreen');

                expect(fullScreenControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Fill browser',
                    'aria-disabled': 'false'
                });
            });
        });

        it('updates ARIA on state change', function () {
            expect().toBe();
        });

        it('can destroy itself', function () {
            expect().toBe();
        });

    });
}).call(this, window.WAIT_TIMEOUT);
