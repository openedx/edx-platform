(function (undefined) {
    describe('VideoCaption', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);

            state = jasmine.initializePlayer();

            videoControl = state.videoControl;

            $.fn.scrollTo.reset();
        });

        afterEach(function () {
            $('.subtitles').remove();

            // `source` tags should be removed to avoid memory leak bug that we
            // had before. Removing of `source` tag, not `video` tag, stops
            // loading video source and clears the memory.
            $('source').remove();

            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            describe('always', function () {
                beforeEach(function () {
                    spyOn($, 'ajaxWithPrefix').andCallThrough();

                    state = jasmine.initializePlayer();

                    videoControl = state.videoControl;

                    $.fn.scrollTo.reset();
                });

                it('create the caption element', function () {
                    expect($('.video')).toContain('ol.subtitles');
                });

                it('add caption control to video player', function () {
                    expect($('.video')).toContain('a.hide-subtitles');
                });

                it('add ARIA attributes to caption control', function () {
                    var captionControl = $('a.hide-subtitles');
                    expect(captionControl).toHaveAttrs({
                        'role': 'button',
                        'title': 'Turn off captions',
                        'aria-disabled': 'false'
                    });
                });

                it('fetch the caption', function () {
                    waitsFor(function () {
                        if (state.videoCaption.loaded === true) {
                            return true;
                        }

                        return false;
                    }, 'Expect captions to be loaded.', WAIT_TIMEOUT);

                    runs(function () {
                        expect($.ajaxWithPrefix).toHaveBeenCalledWith({
                            url: state.videoCaption.captionURL(),
                            notifyOnError: false,
                            data: {
                                videoId: 'Z5KLxerq05Y',
                                language: 'en'
                            },
                            success: jasmine.any(Function),
                            error: jasmine.any(Function)
                        });
                    });
                });

                it('bind window resize event', function () {
                    expect($(window)).toHandleWith(
                        'resize', state.videoCaption.resize
                    );
                });

                it('bind the hide caption button', function () {
                    expect($('.hide-subtitles')).toHandleWith(
                        'click', state.videoCaption.toggle
                    );
                });
            });

            describe('when on a non touch-based device', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();

                    videoControl = state.videoControl;

                    $.fn.scrollTo.reset();
                });

                it('render the caption', function () {
                    var captionsData;

                    captionsData = jasmine.stubbedCaption;
                    $('.subtitles li[data-index]').each(
                        function (index, link) {

                        expect($(link)).toHaveData('index', index);
                        expect($(link)).toHaveData(
                            'start', captionsData.start[index]
                        );
                        expect($(link)).toHaveAttr('tabindex', 0);
                        expect($(link)).toHaveText(captionsData.text[index]);
                    });
                });

                it('add a padding element to caption', function () {
                    expect($('.subtitles li:first').hasClass('spacing'))
                        .toBe(true);
                    expect($('.subtitles li:last').hasClass('spacing'))
                        .toBe(true);
                });

                it('set rendered to true', function () {
                    expect(state.videoCaption.rendered).toBeTruthy();
                });
            });

            describe('when on a touch-based device', function () {
                beforeEach(function () {
                    window.onTouchBasedDevice.andReturn(['iPad']);

                    state = jasmine.initializePlayer();

                    videoControl = state.videoControl;

                    $.fn.scrollTo.reset();
                });

                it('show explaination message', function () {
                    expect($('.subtitles li')).toHaveHtml(
                        'Caption will be displayed when you start playing ' +
                        'the video.'
                    );
                });

                it('does not set rendered to true', function () {
                    expect(state.videoCaption.rendered).toBeFalsy();
                });
            });

            describe('when no captions file was specified', function () {
                beforeEach(function () {
                    loadFixtures('video_all.html');

                    // Unspecify the captions file.
                    $('#example').find('#video_id').data('sub', '');

                    state = new Video('#example');
                });

                it('captions panel is not shown', function () {
                    expect(state.videoCaption.hideSubtitlesEl).toBeHidden();
                });
            });
        });

        describe('search', function () {
            it('return a correct caption index', function () {
                expect(state.videoCaption.search(0)).toEqual(-1);
                expect(state.videoCaption.search(3120)).toEqual(1);
                expect(state.videoCaption.search(6270)).toEqual(2);
                expect(state.videoCaption.search(8490)).toEqual(2);
                expect(state.videoCaption.search(21620)).toEqual(4);
                expect(state.videoCaption.search(24920)).toEqual(5);
            });
        });

        describe('play', function () {
            describe('when the caption was not rendered', function () {
                beforeEach(function () {
                    window.onTouchBasedDevice.andReturn(['iPad']);

                    state = jasmine.initializePlayer();

                    videoControl = state.videoControl;

                    $.fn.scrollTo.reset();

                    state.videoCaption.play();
                });

                it('render the caption', function () {
                    var captionsData;

                    captionsData = jasmine.stubbedCaption;
                    $('.subtitles li[data-index]').each(
                        function (index, link) {

                        expect($(link)).toHaveData('index', index);
                        expect($(link)).toHaveData(
                            'start', captionsData.start[index]
                        );
                        expect($(link)).toHaveAttr('tabindex', 0);
                        expect($(link)).toHaveText(captionsData.text[index]);
                    });
                });

                it('add a padding element to caption', function () {
                    expect($('.subtitles li:first')).toBe('.spacing');
                    expect($('.subtitles li:last')).toBe('.spacing');
                });

                it('set rendered to true', function () {
                    expect(state.videoCaption.rendered).toBeTruthy();
                });

                it('set playing to true', function () {
                    expect(state.videoCaption.playing).toBeTruthy();
                });
            });
        });

        describe('pause', function () {
            beforeEach(function () {
                state.videoCaption.playing = true;
                state.videoCaption.pause();
            });

            it('set playing to false', function () {
                expect(state.videoCaption.playing).toBeFalsy();
            });
        });

        describe('updatePlayTime', function () {
            describe('when the video speed is 1.0x', function () {
                beforeEach(function () {
                    state.videoSpeedControl.currentSpeed = '1.0';
                    state.videoCaption.updatePlayTime(25.000);
                });

                it('search the caption based on time', function () {
                    expect(state.videoCaption.currentIndex).toEqual(5);
                });
            });

            describe('when the video speed is not 1.0x', function () {
                beforeEach(function () {
                    state.videoSpeedControl.currentSpeed = '0.75';
                    state.videoCaption.updatePlayTime(25.000);
                });

                it('search the caption based on 1.0x speed', function () {
                    expect(state.videoCaption.currentIndex).toEqual(5);
                });
            });

            describe('when the index is not the same', function () {
                beforeEach(function () {
                    state.videoCaption.currentIndex = 1;
                    $('.subtitles li[data-index=5]').addClass('current');
                    state.videoCaption.updatePlayTime(25.000);
                });

                it('deactivate the previous caption', function () {
                    expect($('.subtitles li[data-index=1]'))
                        .not.toHaveClass('current');
                });

                it('activate new caption', function () {
                    expect($('.subtitles li[data-index=5]'))
                        .toHaveClass('current');
                });

                it('save new index', function () {
                    expect(state.videoCaption.currentIndex).toEqual(5);
                });

                // Disabled 11/25/13 due to flakiness in master
                xit('scroll caption to new position', function () {
                    expect($.fn.scrollTo).toHaveBeenCalled();
                });
            });

            describe('when the index is the same', function () {
                beforeEach(function () {
                    state.videoCaption.currentIndex = 1;
                    $('.subtitles li[data-index=3]').addClass('current');
                    state.videoCaption.updatePlayTime(15.000);
                });

                it('does not change current subtitle', function () {
                    expect($('.subtitles li[data-index=3]'))
                        .toHaveClass('current');
                });
            });
        });

        describe('resize', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                videoControl = state.videoControl;

                $.fn.scrollTo.reset();

                $('.subtitles li[data-index=1]').addClass('current');
                state.videoCaption.resize();
            });

            describe('set the height of caption container', function () {
                it('when CC button is enabled', function () {
                    var realHeight = parseInt(
                            $('.subtitles').css('maxHeight'), 10
                        ),
                        shouldBeHeight = $('.video-wrapper').height();

                    // Because of some problems with rounding on different
                    // environments: Linux * Mac * FF * Chrome
                    expect(realHeight).toBeCloseTo(shouldBeHeight, 2);
                });

                it('when CC button is disabled ', function () {
                    var realHeight, videoWrapperHeight, progressSliderHeight,
                        controlHeight, shouldBeHeight;

                    state.captionsHidden = true;
                    state.videoCaption.setSubtitlesHeight();

                    realHeight = parseInt(
                        $('.subtitles').css('maxHeight'), 10
                    );
                    videoWrapperHeight = $('.video-wrapper').height();
                    progressSliderHeight = videoControl.sliderEl.height();
                    controlHeight = videoControl.el.height();
                    shouldBeHeight = videoWrapperHeight -
                        0.5 * progressSliderHeight -
                        controlHeight;

                    expect(realHeight).toBe(shouldBeHeight);
                });
            });

            it('set the height of caption spacing', function () {
                var firstSpacing, lastSpacing;

                firstSpacing = Math.abs(parseInt(
                    $('.subtitles .spacing:first').css('height'), 10
                ));
                lastSpacing = Math.abs(parseInt(
                    $('.subtitles .spacing:last').css('height'), 10
                ));

                expect(firstSpacing - state.videoCaption.topSpacingHeight())
                    .toBeLessThan(1);
                expect(lastSpacing - state.videoCaption.bottomSpacingHeight())
                    .toBeLessThan(1);
            });

            it('scroll caption to new position', function () {
                expect($.fn.scrollTo).toHaveBeenCalled();
            });
        });

        // Disabled 11/25/13 due to flakiness in master
        xdescribe('scrollCaption', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                videoControl = state.videoControl;

                $.fn.scrollTo.reset();
            });

            describe('when frozen', function () {
                beforeEach(function () {
                    state.videoCaption.frozen = true;
                    $('.subtitles li[data-index=1]').addClass('current');
                    state.videoCaption.scrollCaption();
                });

                it('does not scroll the caption', function () {
                    expect($.fn.scrollTo).not.toHaveBeenCalled();
                });
            });

            describe('when not frozen', function () {
                beforeEach(function () {
                    state.videoCaption.frozen = false;
                });

                describe('when there is no current caption', function () {
                    beforeEach(function () {
                        state.videoCaption.scrollCaption();
                    });

                    it('does not scroll the caption', function () {
                        expect($.fn.scrollTo).not.toHaveBeenCalled();
                    });
                });

                describe('when there is a current caption', function () {
                    beforeEach(function () {
                        $('.subtitles li[data-index=1]').addClass('current');
                        state.videoCaption.scrollCaption();
                    });

                    it('scroll to current caption', function () {
                        expect($.fn.scrollTo).toHaveBeenCalled();
                    });
                });
            });
        });

        // Disabled 10/9/13 due to flakiness in master
        xdescribe('seekPlayer', function () {
            describe('when the video speed is 1.0x', function () {
                beforeEach(function () {
                    state.videoSpeedControl.currentSpeed = '1.0';
                    $('.subtitles li[data-start="14910"]').trigger('click');
                });

                it('trigger seek event with the correct time', function () {
                    expect(state.videoPlayer.currentTime).toEqual(14.91);
                });
            });

            describe('when the video speed is not 1.0x', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();

                    videoControl = state.videoControl;

                    $.fn.scrollTo.reset();

                    state.videoSpeedControl.currentSpeed = '0.75';
                    $('.subtitles li[data-start="14910"]').trigger('click');
                });

                it('trigger seek event with the correct time', function () {
                    expect(state.videoPlayer.currentTime).toEqual(14.91);
                });
            });

            describe('when the player type is Flash at speed 0.75x',
                function () {

                beforeEach(function () {
                    state = jasmine.initializePlayer();

                    videoControl = state.videoControl;

                    $.fn.scrollTo.reset();

                    state.videoSpeedControl.currentSpeed = '0.75';
                    state.currentPlayerMode = 'flash';
                    $('.subtitles li[data-start="14910"]').trigger('click');
                });

                it('trigger seek event with the correct time', function () {
                    expect(state.videoPlayer.currentTime).toEqual(15);
                });
            });
        });

        describe('toggle', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                videoControl = state.videoControl;

                $.fn.scrollTo.reset();

                spyOn(state.videoPlayer, 'log');
                $('.subtitles li[data-index=1]').addClass('current');
            });

            describe('when the caption is visible', function () {
                beforeEach(function () {
                    state.el.removeClass('closed');
                    state.videoCaption.toggle(jQuery.Event('click'));
                });

                it('log the hide_transcript event', function () {
                    expect(state.videoPlayer.log).toHaveBeenCalledWith(
                        'hide_transcript',
                        {
                            currentTime: state.videoPlayer.currentTime
                        }
                    );
                });

                it('hide the caption', function () {
                    expect(state.el).toHaveClass('closed');
                });

                it('changes ARIA attribute of caption control', function () {
                    expect($('a.hide-subtitles'))
                        .toHaveAttr('title', 'Turn on captions');
                });
            });

            describe('when the caption is hidden', function () {
                beforeEach(function () {
                    state.el.addClass('closed');
                    state.videoCaption.toggle(jQuery.Event('click'));

                    jasmine.Clock.useMock();
                });

                it('log the show_transcript event', function () {
                    expect(state.videoPlayer.log).toHaveBeenCalledWith(
                        'show_transcript',
                        {
                            currentTime: state.videoPlayer.currentTime
                        }
                    );
                });

                it('show the caption', function () {
                    expect(state.el).not.toHaveClass('closed');
                });

                it('changes ARIA attribute of caption control', function () {
                    expect($('a.hide-subtitles'))
                        .toHaveAttr('title', 'Turn off captions');
                });

                // Test turned off due to flakiness (11/25/13)
                xit('scroll the caption', function () {
                    // After transcripts are shown, and the video plays for a
                    // bit.
                    jasmine.Clock.tick(1000);

                    // The transcripts should have advanced by at least one
                    // position. When they advance, the list scrolls. The
                    // current transcript position should be constantly
                    // visible.
                    runs(function () {
                        expect($.fn.scrollTo).toHaveBeenCalled();
                    });
                });
            });
        });

        describe('caption accessibility', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();

                videoControl = state.videoControl;

                $.fn.scrollTo.reset();
            });

            describe('when getting focus through TAB key', function () {
                beforeEach(function () {
                    state.videoCaption.isMouseFocus = false;
                    $('.subtitles li[data-index=0]').trigger(
                        jQuery.Event('focus')
                    );
                });

                it('shows an outline around the caption', function () {
                    expect($('.subtitles li[data-index=0]'))
                        .toHaveClass('focused');
                });

                it('has automatic scrolling disabled', function () {
                    expect(state.videoCaption.autoScrolling).toBe(false);
                });
            });

            describe('when loosing focus through TAB key', function () {
                beforeEach(function () {
                    $('.subtitles li[data-index=0]').trigger(
                        jQuery.Event('blur')
                    );
                });

                it('does not show an outline around the caption', function () {
                    expect($('.subtitles li[data-index=0]'))
                        .not.toHaveClass('focused');
                });

                it('has automatic scrolling enabled', function () {
                    expect(state.videoCaption.autoScrolling).toBe(true);
                });
            });

            describe(
                'when same caption gets the focus through mouse after ' +
                'having focus through TAB key',
                function () {

                beforeEach(function () {
                    state.videoCaption.isMouseFocus = false;
                    $('.subtitles li[data-index=0]')
                        .trigger(jQuery.Event('focus'));
                    $('.subtitles li[data-index=0]')
                        .trigger(jQuery.Event('mousedown'));
                });

                it('does not show an outline around it', function () {
                    expect($('.subtitles li[data-index=0]'))
                        .not.toHaveClass('focused');
                });

                it('has automatic scrolling enabled', function () {
                    expect(state.videoCaption.autoScrolling).toBe(true);
                });
            });

            describe(
                'when a second caption gets focus through mouse after ' +
                'first had focus through TAB key',
                function () {

                var subDataLiIdx__0, subDataLiIdx__1;

                beforeEach(function () {
                    subDataLiIdx__0 = $('.subtitles li[data-index=0]');
                    subDataLiIdx__1 = $('.subtitles li[data-index=1]');

                    state.videoCaption.isMouseFocus = false;

                    subDataLiIdx__0.trigger(jQuery.Event('focus'));
                    subDataLiIdx__0.trigger(jQuery.Event('blur'));

                    state.videoCaption.isMouseFocus = true;

                    subDataLiIdx__1.trigger(jQuery.Event('mousedown'));
                });

                it('does not show an outline around the first', function () {
                    expect(subDataLiIdx__0).not.toHaveClass('focused');
                });

                it('does not show an outline around the second', function () {
                    expect(subDataLiIdx__1).not.toHaveClass('focused');
                });

                it('has automatic scrolling enabled', function () {
                    expect(state.videoCaption.autoScrolling).toBe(true);
                });
            });
        });
    });

}).call(this);
