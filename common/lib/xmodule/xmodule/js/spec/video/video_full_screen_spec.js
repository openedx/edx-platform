(function () {
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
            state.videoPlayer.destroy();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
            });

            it('renders the fullscreen control', function () {
                expect($('.add-fullscreen')).toExist();
                expect(state.videoFullScreen.fullScreenState).toBe(false);
            });

            it('correctly adds ARIA attributes to fullscreen control', function () {
                var fullScreenControl = $('.add-fullscreen');

                expect(fullScreenControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Fill browser',
                    'aria-disabled': 'false'
                });
            });

            it('correctly triggers the event handler to toggle fullscreen mode', function () {
                spyOn(state.videoFullScreen, 'exit');
                spyOn(state.videoFullScreen, 'enter');

                state.videoFullScreen.fullScreenState = false;
                state.videoFullScreen.toggle();
                expect(state.videoFullScreen.enter).toHaveBeenCalled();

                state.videoFullScreen.fullScreenState = true;
                state.videoFullScreen.toggle();
                expect(state.videoFullScreen.exit).toHaveBeenCalled();
            });

            it('correctly updates ARIA on state change', function () {
                var fullScreenControl = $('.add-fullscreen');
                fullScreenControl.click();
                expect(fullScreenControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Exit full browser',
                    'aria-disabled': 'false'
                });
                fullScreenControl.click();
                expect(fullScreenControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'Fill browser',
                    'aria-disabled': 'false'
                });
            });

            it('correctly can out of fullscreen by pressing esc', function () {
                spyOn(state.videoCommands, 'execute');
                var esc = $.Event('keyup');
                esc.keyCode = 27;
                state.isFullScreen = true;
                $(document).trigger(esc);
                expect(state.videoCommands.execute).toHaveBeenCalledWith('toggleFullScreen');
            });

            it('can update video dimensions on state change', function () {
                state.el.trigger('fullscreen', [true]);
                expect(state.resizer.setMode).toHaveBeenCalledWith('both');
                state.el.trigger('fullscreen', [false]);
                expect(state.resizer.setMode).toHaveBeenCalledWith('width');
            });

            it('can destroy itself', function () {
                state.videoFullScreen.destroy();
                expect($('.add-fullscreen')).not.toExist();
                expect(state.videoFullScreen).toBeUndefined();
            });
        });

        it('Controls height is actual on switch to fullscreen', function () {
            spyOn($.fn, 'height').andCallFake(function (val) {
                return _.isUndefined(val) ? 100: this;
            });

            state = jasmine.initializePlayer();
            $(state.el).trigger('fullscreen');

            expect(state.videoFullScreen.height).toBe(150);
        });
    });
}).call(this);
