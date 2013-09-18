(function () {
    describe('Video FocusGrabber', function () {
        var state;

        beforeEach(function () {
            loadFixtures('video_html5.html');
            state = new Video('#example');

            spyOnEvent(state.el, 'mousemove');
            spyOn(state.focusGrabber, 'disableFocusGrabber').andCallThrough();
            spyOn(state.focusGrabber, 'enableFocusGrabber').andCallThrough();
        });

        it('check existence of focus grabber elements and their position', function () {
            var firstFGEl = state.el.find('.focus_grabber.first'),
                lastFGEl = state.el.find('.focus_grabber.last'),
                tcWrapperEl = state.el.find('.tc-wrapper');

            // Existence check.
            expect(firstFGEl.length).toBe(1);
            expect(lastFGEl.length).toBe(1);

            // Position check.
            expect(firstFGEl.index() + 1).toBe(tcWrapperEl.index());
            expect(lastFGEl.index() - 1).toBe(tcWrapperEl.index());
        });

        it('from the start, focus grabbers are disabled', function () {
            expect(state.focusGrabber.elFirst.attr('tabindex')).toBe(-1);
            expect(state.focusGrabber.elLast.attr('tabindex')).toBe(-1);
        });

        it('when first focus grabber is focused "mousemove" event is triggered, grabbers are disabled', function () {
            state.focusGrabber.elFirst.focus();

            expect('mousemove').toHaveBeenTriggeredOn(state.el);
            expect(state.focusGrabber.disableFocusGrabber).toHaveBeenCalled();
        });

        it('when last focus grabber is focused "mousemove" event is triggered, grabbers are disabled', function () {
            state.focusGrabber.elLast.focus();

            expect('mousemove').toHaveBeenTriggeredOn(state.el);
            expect(state.focusGrabber.disableFocusGrabber).toHaveBeenCalled();
        });

        it('after controls autohide focus grabbers are enabled', function () {
            runs(function () {
                console.log('focus 1: a');
                state.videoCaption.hideCaptions(true);
                state.el.trigger('mousemove');
                console.log('focus 1: b');
            });

            waits(2 * (state.videoControl.fadeOutTimeout + 100));

            runs(function () {
                expect(state.focusGrabber.enableFocusGrabber).toHaveBeenCalled();
            });
        });
    });
}).call(this);
