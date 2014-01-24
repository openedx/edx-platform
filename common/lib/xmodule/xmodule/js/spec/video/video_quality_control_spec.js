(function (undefined) {
    describe('VideoQualityControl', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice')
                .andReturn(null);
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer('video.html');
            });

            it('render the quality control', function () {
                var container = state.videoControl.secondaryControlsEl;

                expect(container).toContain('a.quality_control');
            });

            it('add ARIA attributes to quality control', function () {
                var qualityControl = $('a.quality_control');

                expect(qualityControl).toHaveAttrs({
                    'role': 'button',
                    'title': 'HD off',
                    'aria-disabled': 'false'
                });
            });

            it('bind the quality control', function () {
                var handler = state.videoQualityControl.toggleQuality;

                expect($('a.quality_control')).toHandleWith('click', handler);
            });
        });
    });
}).call(this);
