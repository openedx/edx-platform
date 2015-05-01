(function (undefined) {
    describe('VideoCaption', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice')
                .andReturn(null);

            $.fn.scrollTo.reset();
        });

        afterEach(function () {
            // `source` tags should be removed to avoid memory leak bug that we
            // had before. Removing of `source` tag, not `video` tag, stops
            // loading video source and clears the memory.
            $('source').remove();
            $.fn.scrollTo.reset();
            state.storage.clear();
            state.videoPlayer.destroy();

            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            describe('always', function () {
                beforeEach(function () {
                    spyOn($, 'ajaxWithPrefix').andCallThrough();
                });

                it('create the caption element', function () {
                    state = jasmine.initializePlayer();
                    expect($('.video')).toContain('ol.subtitles');
                });

                it('add caption control to video player', function () {
                    state = jasmine.initializePlayer();
                    expect($('.video')).toContain('a.hide-subtitles');
                });

                it('add ARIA attributes to caption control', function () {
                    state = jasmine.initializePlayer();
                    var captionControl = $('a.hide-subtitles');
                    expect(captionControl).toHaveAttrs({
                        'role': 'button',
                        'title': 'Turn off captions',
                        'aria-disabled': 'false'
                    });
                });

                it('fetch the caption in HTML5 mode', function () {
                    runs(function () {
                        state = jasmine.initializePlayer();
                    });

                    waitsFor(function () {
                        return state.videoCaption.loaded;
                    }, 'Expect captions to be loaded.', WAIT_TIMEOUT);

                    runs(function () {
                        expect($.ajaxWithPrefix).toHaveBeenCalledWith({
                            url: '/transcript/translation/en',
                            notifyOnError: false,
                            data: void(0),
                            success: jasmine.any(Function),
                            error: jasmine.any(Function)
                        });
                        expect($.ajaxWithPrefix.mostRecentCall.args[0].data)
                            .toBeUndefined();
                    });
                });

                it('fetch the caption in Flash mode', function () {
                    runs(function () {
                        state = jasmine.initializePlayerYouTube();
                        spyOn(state, 'isFlashMode').andReturn(true);
                        state.videoCaption.fetchCaption();
                    });

                    waitsFor(function () {
                        return state.videoCaption.loaded;
                    }, 'Expect captions to be loaded.', WAIT_TIMEOUT);

                    runs(function () {
                        expect($.ajaxWithPrefix).toHaveBeenCalledWith({
                            url: '/transcript/translation/en',
                            notifyOnError: false,
                            data: jasmine.any(Object),
                            success: jasmine.any(Function),
                            error: jasmine.any(Function)
                        });
                        expect($.ajaxWithPrefix.mostRecentCall.args[0].data)
                            .toEqual({
                                videoId: 'cogebirgzzM'
                            });
                    });
                });

                it('fetch the caption in Youtube mode', function () {
                    runs(function () {
                        state = jasmine.initializePlayerYouTube();
                    });

                    waitsFor(function () {
                        return state.videoCaption.loaded;
                    }, 'Expect captions to be loaded.', WAIT_TIMEOUT);

                    runs(function () {
                        expect($.ajaxWithPrefix).toHaveBeenCalledWith({
                            url: '/transcript/translation/en',
                            notifyOnError: false,
                            data: jasmine.any(Object),
                            success: jasmine.any(Function),
                            error: jasmine.any(Function)
                        });
                        expect($.ajaxWithPrefix.mostRecentCall.args[0].data)
                            .toEqual({
                                videoId: 'cogebirgzzM'
                            });
                    });
                });

                it('bind the mouse movement', function () {
                    state = jasmine.initializePlayer();
                    expect($('.subtitles')).toHandle('mouseover');
                    expect($('.subtitles')).toHandle('mouseout');
                    expect($('.subtitles')).toHandle('mousemove');
                    expect($('.subtitles')).toHandle('mousewheel');
                    expect($('.subtitles')).toHandle('DOMMouseScroll');
                 });

                 it('bind the scroll', function () {
                    state = jasmine.initializePlayer();
                    expect($('.subtitles'))
                        .toHandleWith('scroll', state.videoControl.showControls);
                 });

            });

            it('can destroy itself', function () {
                spyOn($, 'ajaxWithPrefix');
                state = jasmine.initializePlayer();
                var plugin = state.videoCaption;

                spyOn($.fn, 'off').andCallThrough();
                state.videoCaption.destroy();

                expect(state.videoCaption).toBeUndefined();
                expect($.fn.off).toHaveBeenCalledWith({
                    'caption:fetch': plugin.fetchCaption,
                    'caption:resize': plugin.onResize,
                    'caption:update': plugin.onCaptionUpdate,
                    'ended': plugin.pause,
                    'fullscreen': plugin.onResize,
                    'pause': plugin.pause,
                    'play': plugin.play,
                    'destroy': plugin.destroy
                });
            });

            describe('renderLanguageMenu', function () {
                describe('is rendered', function () {
                    it('if languages more than 1', function () {
                        state = jasmine.initializePlayer();
                        var transcripts = state.config.transcriptLanguages,
                            langCodes = _.keys(transcripts),
                            langLabels = _.values(transcripts);

                        expect($('.langs-list')).toExist();
                        expect($('.langs-list')).toHandle('click');


                        $('.langs-list li').each(function(index) {
                            var code = $(this).data('lang-code'),
                                link = $(this).find('a'),
                                label = link.text();

                            expect(code).toBeInArray(langCodes);
                            expect(label).toBeInArray(langLabels);
                        });
                    });

                    it('when clicking on link with new language', function () {
                        state = jasmine.initializePlayer();
                        var Caption = state.videoCaption,
                            link = $('.langs-list li[data-lang-code="de"] a');

                        spyOn(Caption, 'fetchCaption');
                        spyOn(state.storage, 'setItem');

                        state.lang = 'en';
                        link.trigger('click');

                        expect(Caption.fetchCaption).toHaveBeenCalled();
                        expect(state.lang).toBe('de');
                        expect(state.storage.setItem)
                            .toHaveBeenCalledWith('language', 'de');
                        expect($('.langs-list li.is-active').length).toBe(1);
                    });

                    it('when clicking on link with current language', function () {
                        state = jasmine.initializePlayer();
                        var Caption = state.videoCaption,
                            link = $('.langs-list li[data-lang-code="en"] a');

                        spyOn(Caption, 'fetchCaption');
                        spyOn(state.storage, 'setItem');

                        state.lang = 'en';
                        link.trigger('click');

                        expect(Caption.fetchCaption).not.toHaveBeenCalled();
                        expect(state.lang).toBe('en');
                        expect(state.storage.setItem)
                            .not.toHaveBeenCalledWith('language', 'en');
                        expect($('.langs-list li.is-active').length).toBe(1);
                    });

                    it('open the language toggle on hover', function () {
                        state = jasmine.initializePlayer();
                        $('.lang').mouseenter();
                        expect($('.lang')).toHaveClass('is-opened');
                        $('.lang').mouseleave();
                        expect($('.lang')).not.toHaveClass('is-opened');
                    });
                });

                describe('is not rendered', function () {
                    it('if just 1 language', function () {
                        state = jasmine.initializePlayer(null, {
                            'transcriptLanguages': {"en": "English"}
                        });

                        expect($('.langs-list')).not.toExist();
                        expect($('.lang')).not.toHandle('mouseenter');
                        expect($('.lang')).not.toHandle('mouseleave');
                    });
                });
            });

            describe('when on a non touch-based device', function () {
                beforeEach(function () {
                    runs(function () {
                        state = jasmine.initializePlayer();
                    });

                    waitsFor(function () {
                        return state.videoCaption.rendered;
                    }, 'Captions are not rendered', WAIT_TIMEOUT);
                });

                it('render the caption', function () {
                    runs(function () {
                        var captionsData = jasmine.stubbedCaption,
                        items = $('.subtitles li[data-index]');

                        _.each(captionsData.text, function (text, index) {
                            var item = items.eq(index);

                            expect(item).toHaveData('index', index);
                            expect(item).toHaveData(
                                'start', captionsData.start[index]
                            );
                            expect(item).toHaveAttr('tabindex', 0);
                            expect(item).toHaveText(text);
                        });
                    });
                });

                it('add a padding element to caption', function () {
                    runs(function () {
                        expect($('.subtitles li:first').hasClass('spacing'))
                            .toBe(true);
                        expect($('.subtitles li:last').hasClass('spacing'))
                            .toBe(true);
                    });
                });


                it('bind all the caption link', function () {
                    runs(function () {
                        var handlerList = ['captionMouseOverOut', 'captionClick',
                            'captionMouseDown', 'captionFocus', 'captionBlur',
                            'captionKeyDown'
                        ];

                        $.each(handlerList, function(index, handler) {
                            spyOn(state.videoCaption, handler);
                        });
                        $('.subtitles li[data-index]').each(
                            function (index, link) {


                            $(link).trigger('mouseover');
                            expect(state.videoCaption.captionMouseOverOut).toHaveBeenCalled();

                            state.videoCaption.captionMouseOverOut.reset();
                            $(link).trigger('mouseout');
                            expect(state.videoCaption.captionMouseOverOut).toHaveBeenCalled();

                            $(this).click();
                            expect(state.videoCaption.captionClick).toHaveBeenCalled();

                            $(this).trigger('mousedown');
                            expect(state.videoCaption.captionMouseDown).toHaveBeenCalled();

                            $(this).trigger('focus');
                            expect(state.videoCaption.captionFocus).toHaveBeenCalled();

                            $(this).trigger('blur');
                            expect(state.videoCaption.captionBlur).toHaveBeenCalled();

                            $(this).trigger('keydown');
                            expect(state.videoCaption.captionKeyDown).toHaveBeenCalled();
                        });
                    });
                });

                it('set rendered to true', function () {
                    runs(function () {
                        state = jasmine.initializePlayer();
                    });

                    waitsFor(function () {
                        return state.videoCaption.rendered;
                    }, 'Captions are not rendered', WAIT_TIMEOUT);

                    runs(function () {
                        expect(state.videoCaption.rendered).toBeTruthy();
                    });
                });
            });

            describe('when on a touch-based device', function () {
                beforeEach(function () {
                    window.onTouchBasedDevice.andReturn(['iPad']);

                    state = jasmine.initializePlayer();
                    $.fn.scrollTo.reset();
                });

                it('show explanation message', function () {
                    expect($('.subtitles li')).toHaveHtml(
                        'Caption will be displayed when you start playing ' +
                        'the video.'
                    );
                });

                it('show captions on play', function () {
                    runs(function () {
                        state.el.trigger('play');
                    });

                    waitsFor(function () {
                        return state.videoCaption.rendered;
                    }, 'Captions are not rendered', WAIT_TIMEOUT);

                    runs(function () {
                        var captionsData = jasmine.stubbedCaption,
                        items = $('.subtitles li[data-index]');

                        _.each(captionsData.text, function (text, index) {
                            var item = items.eq(index);

                            expect(item).toHaveData('index', index);
                            expect(item).toHaveData(
                                'start', captionsData.start[index]
                            );
                            expect(item).toHaveAttr('tabindex', 0);
                            expect(item).toHaveText(text);
                        });
                    });
                });

                it('does not set rendered to true', function () {
                    expect(state.videoCaption.rendered).toBeFalsy();
                });
            });

            describe('when no captions file was specified', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer('video_all.html', {
                        'sub': '',
                        'transcriptLanguages': {},
                    });
                });

                it('captions panel is not shown', function () {
                    expect(state.videoCaption.hideSubtitlesEl).toBeHidden();
                });
            });
        });

        describe('mouse movement', function () {
            beforeEach(function () {
                jasmine.Clock.useMock();
                spyOn(window, 'clearTimeout');

                runs(function () {
                    state = jasmine.initializePlayer();
                    jasmine.Clock.tick(50);
                });

                waitsFor(function () {
                    return state.videoCaption.rendered;
                }, 'Captions are not rendered', WAIT_TIMEOUT);
            });

            describe('when cursor is outside of the caption box', function () {
                it('does not set freezing timeout', function () {
                    runs(function () {
                        expect(state.videoCaption.frozen).toBeFalsy();
                    });
                });
            });

            describe('when cursor is in the caption box', function () {
                beforeEach(function () {
                    spyOn(state.videoCaption, 'onMouseLeave');
                    runs(function () {
                        $(window).trigger(jQuery.Event('mousemove'));
                        jasmine.Clock.tick(state.config.captionsFreezeTime);
                        $('.subtitles').trigger(jQuery.Event('mouseenter'));
                        jasmine.Clock.tick(state.config.captionsFreezeTime);
                    });
                });

                it('set the freezing timeout', function () {
                    runs(function () {
                        expect(state.videoCaption.frozen).not.toBeFalsy();
                        expect(state.videoCaption.onMouseLeave).toHaveBeenCalled();
                    });
                });

                describe('when the cursor is moving', function () {
                    it('reset the freezing timeout', function () {
                        runs(function () {
                            $('.subtitles').trigger(jQuery.Event('mousemove'));
                            expect(window.clearTimeout).toHaveBeenCalled();
                        });
                    });
                });

                describe('when the mouse is scrolling', function () {
                    it('reset the freezing timeout', function () {
                        runs(function () {
                            $('.subtitles').trigger(jQuery.Event('mousewheel'));
                            expect(window.clearTimeout).toHaveBeenCalled();
                        });
                    });
                });
            });

            describe(
                'when cursor is moving out of the caption box',
                function () {

                beforeEach(function () {
                    state.videoCaption.frozen = 100;
                    $.fn.scrollTo.reset();
                });

                describe('always', function () {
                    beforeEach(function () {
                        $('.subtitles').trigger(jQuery.Event('mouseout'));
                    });

                    it('reset the freezing timeout', function () {
                        expect(window.clearTimeout).toHaveBeenCalledWith(100);
                    });

                    it('unfreeze the caption', function () {
                        expect(state.videoCaption.frozen).toBeNull();
                    });
                });

                describe('when the player is playing', function () {
                    beforeEach(function () {
                        state.videoCaption.playing = true;
                        $('.subtitles li[data-index]:first')
                            .addClass('current');
                        $('.subtitles').trigger(jQuery.Event('mouseout'));
                    });

                    it('scroll the caption', function () {
                        expect($.fn.scrollTo).toHaveBeenCalled();
                    });
                });

                describe('when the player is not playing', function () {
                    beforeEach(function () {
                        state.videoCaption.playing = false;
                        $('.subtitles').trigger(jQuery.Event('mouseout'));
                    });

                    it('does not scroll the caption', function () {
                        expect($.fn.scrollTo).not.toHaveBeenCalled();
                    });
                });
            });
        });

        describe('fetchCaption', function () {
            var Caption, msg;

            beforeEach(function () {
                state = jasmine.initializePlayer();
                Caption = state.videoCaption;
                spyOn($, 'ajaxWithPrefix').andCallThrough();
                spyOn(Caption, 'renderCaption');
                spyOn(Caption, 'bindHandlers');
                spyOn(Caption, 'updatePlayTime');
                spyOn(Caption, 'hideCaptions');
                spyOn(state, 'youtubeId').andReturn('Z5KLxerq05Y');
            });

            it('show caption on language change', function () {
                Caption.loaded = true;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.hideCaptions).toHaveBeenCalledWith(false);
            });

            msg = 'use cookie to show/hide captions if they have not been ' +
                    'loaded yet';
            it(msg, function () {
                Caption.loaded = false;
                state.hide_captions = false;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.hideCaptions).toHaveBeenCalledWith(false, false);

                Caption.loaded = false;
                Caption.hideCaptions.reset();
                state.hide_captions = true;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.hideCaptions).toHaveBeenCalledWith(true, false);
            });

            it('on success: on touch devices', function () {
                state.isTouch = true;
                Caption.loaded = false;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.bindHandlers).toHaveBeenCalled();
                expect(Caption.renderCaption).not.toHaveBeenCalled();
                expect(Caption.updatePlayTime).not.toHaveBeenCalled();
                expect(Caption.loaded).toBeTruthy();
            });

            msg = 'on success: change language on touch devices when ' +
                 'captions have not been rendered yet';
            it(msg, function () {
                state.isTouch = true;
                Caption.loaded = true;
                Caption.rendered = false;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.bindHandlers).not.toHaveBeenCalled();
                expect(Caption.renderCaption).not.toHaveBeenCalled();
                expect(Caption.updatePlayTime).not.toHaveBeenCalled();
                expect(Caption.loaded).toBeTruthy();
            });

            it('on success: re-render on touch devices', function () {
                state.isTouch = true;
                Caption.loaded = true;
                Caption.rendered = true;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.bindHandlers).not.toHaveBeenCalled();
                expect(Caption.renderCaption).toHaveBeenCalled();
                expect(Caption.updatePlayTime).toHaveBeenCalled();
                expect(Caption.loaded).toBeTruthy();
            });

            it('on success: rendered correct', function () {
                Caption.loaded = false;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.bindHandlers).toHaveBeenCalled();
                expect(Caption.renderCaption).toHaveBeenCalled();
                expect(Caption.updatePlayTime).not.toHaveBeenCalled();
                expect(Caption.loaded).toBeTruthy();
            });

            it('on success: re-rendered correct', function () {
                Caption.loaded = true;
                Caption.rendered = true;
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.bindHandlers).not.toHaveBeenCalled();
                expect(Caption.renderCaption).toHaveBeenCalled();
                expect(Caption.updatePlayTime).toHaveBeenCalled();
                expect(Caption.loaded).toBeTruthy();
            });

            msg = 'on error: captions are hidden if there are no transcripts';
            it(msg, function () {
                spyOn(Caption, 'fetchAvailableTranslations');
                $.ajax.andCallFake(function (settings) {
                    _.result(settings, 'error');
                });

                state.config.transcriptLanguages = {};

                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.fetchAvailableTranslations).not.toHaveBeenCalled();
                expect(Caption.hideCaptions.mostRecentCall.args)
                    .toEqual([true, false]);
                expect(Caption.hideSubtitlesEl).toBeHidden();
            });

            msg = 'on error: fetch available translations if there are ' +
                    'additional transcripts';
            xit(msg, function () {
                $.ajax
                    .andCallFake(function (settings) {
                        _.result(settings, 'error');
                    });

                state.config.transcriptLanguages = {
                    'en': 'English',
                    'uk': 'Ukrainian',
                };

                spyOn(Caption, 'fetchAvailableTranslations');
                Caption.fetchCaption();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.fetchAvailableTranslations).toHaveBeenCalled();
                expect(Caption.hideCaptions).not.toHaveBeenCalled();
            });
        });

        describe('fetchAvailableTranslations', function () {
            var Caption, msg;

            beforeEach(function () {
                state = jasmine.initializePlayer();
                Caption = state.videoCaption;
                spyOn($, 'ajaxWithPrefix').andCallThrough();
                spyOn(Caption, 'hideCaptions');
                spyOn(Caption, 'fetchCaption');
                spyOn(Caption, 'renderLanguageMenu');
            });

            it('request created with correct parameters', function () {
                Caption.fetchAvailableTranslations();

                expect($.ajaxWithPrefix).toHaveBeenCalledWith({
                    url: '/transcript/available_translations',
                    notifyOnError: false,
                    success: jasmine.any(Function),
                    error: jasmine.any(Function)
                });
            });

            msg = 'on succes: language menu is rendered if translations available';
            it(msg, function () {
                state.config.transcriptLanguages = {
                    'en': 'English',
                    'uk': 'Ukrainian',
                    'de': 'German'
                };
                Caption.fetchAvailableTranslations();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.fetchCaption).toHaveBeenCalled();
                expect(state.config.transcriptLanguages).toEqual({
                    'uk': 'Ukrainian',
                    'de': 'German'
                });
                expect(Caption.renderLanguageMenu).toHaveBeenCalledWith({
                    'uk': 'Ukrainian',
                    'de': 'German'
                });
            });

            msg = 'on succes: language menu isn\'t rendered if translations unavailable';
            it(msg, function () {
                state.config.transcriptLanguages = {
                    'en': 'English',
                    'ru': 'Russian'
                };
                Caption.fetchAvailableTranslations();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.fetchCaption).not.toHaveBeenCalled();
                expect(state.config.transcriptLanguages).toEqual({});
                expect(Caption.renderLanguageMenu).not.toHaveBeenCalled();
            });

            msg = 'on error: captions are hidden if there are no transcript';
            it(msg, function () {
                $.ajax.andCallFake(function (settings) {
                    _.result(settings, 'error');
                });
                Caption.fetchAvailableTranslations();

                expect($.ajaxWithPrefix).toHaveBeenCalled();
                expect(Caption.hideCaptions).toHaveBeenCalledWith(true, false);
                expect(Caption.hideSubtitlesEl).toBeHidden();
            });
        });

        describe('play', function () {
            describe('when the caption was not rendered', function () {
                beforeEach(function () {
                    window.onTouchBasedDevice.andReturn(['iPad']);

                    runs(function () {
                        state = jasmine.initializePlayer();
                        state.videoCaption.play();
                    });

                    waitsFor(function () {
                        return state.videoCaption.rendered;
                    }, 'Captions are not rendered', WAIT_TIMEOUT);
                });

                it('render the caption', function () {
                    runs(function () {
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

                });

                it('add a padding element to caption', function () {
                    runs(function () {
                        expect($('.subtitles li:first')).toBe('.spacing');
                        expect($('.subtitles li:last')).toBe('.spacing');
                    });
                });

                it('set rendered to true', function () {
                    runs(function () {
                        expect(state.videoCaption.rendered).toBeTruthy();
                    });
                });

                it('set playing to true', function () {
                    runs(function () {
                        expect(state.videoCaption.playing).toBeTruthy();
                    });
                });
            });
        });

        describe('pause', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                state.videoCaption.playing = true;
                state.videoCaption.pause();
            });

            it('set playing to false', function () {
                expect(state.videoCaption.playing).toBeFalsy();
            });
        });

        describe('updatePlayTime', function () {
            beforeEach(function () {
                runs(function () {
                    state = jasmine.initializePlayer();
                });

                waitsFor(function () {
                    return state.videoCaption.rendered;
                }, 'Captions are not rendered', WAIT_TIMEOUT);
            });

            describe('when the video speed is 1.0x', function () {
                it('search the caption based on time', function () {
                    runs(function () {
                        state.videoCaption.updatePlayTime(25.000);
                        expect(state.videoCaption.currentIndex).toEqual(5);

                        // Flash mode
                        spyOn(state, 'isFlashMode').andReturn(true);
                        state.speed = '1.0';
                        state.videoCaption.updatePlayTime(25.000);
                        expect(state.videoCaption.currentIndex).toEqual(5);
                    });
                });
            });

            describe('when the video speed is not 1.0x', function () {
                it('search the caption based on 1.0x speed', function () {
                    runs(function () {
                        state.videoCaption.updatePlayTime(25.000);
                        expect(state.videoCaption.currentIndex).toEqual(5);

                        // To test speed, don't use start / end times.
                        state.config.startTime = 0;
                        state.config.endTime = null;

                        // Flash mode
                        state.speed = '2.0';
                        spyOn(state, 'isFlashMode').andReturn(true);
                        state.videoCaption.updatePlayTime(25.000);
                        expect(state.videoCaption.currentIndex).toEqual(9);
                        state.speed = '0.75';
                        state.videoCaption.updatePlayTime(25.000);
                        expect(state.videoCaption.currentIndex).toEqual(3);
                    });
                });
            });

            describe('when the index is not the same', function () {
                beforeEach(function () {
                    runs(function () {
                        state.videoCaption.currentIndex = 1;
                        $('.subtitles li[data-index=5]').addClass('current');
                        state.videoCaption.updatePlayTime(25.000);
                    });
                });

                it('deactivate the previous caption', function () {
                    runs(function () {
                        expect($('.subtitles li[data-index=1]'))
                            .not.toHaveClass('current');
                    });
                });

                it('activate new caption', function () {
                    runs(function () {
                        expect($('.subtitles li[data-index=5]'))
                            .toHaveClass('current');
                    });
                });

                it('save new index', function () {
                    runs(function () {
                        expect(state.videoCaption.currentIndex).toEqual(5);
                    });
                });

                it('scroll caption to new position', function () {
                    runs(function () {
                        expect($.fn.scrollTo).toHaveBeenCalled();
                    });
                });
            });

            describe('when the index is the same', function () {
                it('does not change current subtitle', function () {
                    runs(function () {
                        state.videoCaption.currentIndex = 1;
                        $('.subtitles li[data-index=3]').addClass('current');
                        state.videoCaption.updatePlayTime(15.000);
                        expect($('.subtitles li[data-index=3]'))
                            .toHaveClass('current');
                    });
                });
            });
        });

        describe('resize', function () {
            beforeEach(function () {
                runs(function () {
                    state = jasmine.initializePlayer();
                });

                waitsFor(function () {
                    return state.videoCaption.rendered;
                }, 'Captions are not rendered', WAIT_TIMEOUT);

                runs(function () {
                    videoControl = state.videoControl;
                    $('.subtitles li[data-index=1]').addClass('current');
                    state.videoCaption.onResize();
                });
            });

            describe('set the height of caption container', function () {
                it('when CC button is enabled', function () {
                    runs(function () {
                        var realHeight = parseInt(
                                $('.subtitles').css('maxHeight'), 10
                            ),
                            shouldBeHeight = $('.video-wrapper').height();

                        // Because of some problems with rounding on different
                        // environments: Linux * Mac * FF * Chrome
                        expect(realHeight).toBeCloseTo(shouldBeHeight, 2);
                    });
                });

                it('when CC button is disabled ', function () {
                    runs(function () {
                        var realHeight, videoWrapperHeight, progressSliderHeight,
                            controlHeight, shouldBeHeight;

                        state.captionsHidden = true;
                        state.videoCaption.setSubtitlesHeight();

                        realHeight = parseInt(
                            $('.subtitles').css('maxHeight'), 10
                        );
                        videoWrapperHeight = $('.video-wrapper').height();
                        progressSliderHeight = state.el.find('.slider').height();
                        controlHeight = state.el.find('.video-controls').height();
                        shouldBeHeight = videoWrapperHeight -
                            0.5 * progressSliderHeight -
                            controlHeight;

                        expect(realHeight).toBe(shouldBeHeight);
                    });
                });
            });

            it('set the height of caption spacing', function () {
                runs(function () {
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
            });

            it('scroll caption to new position', function () {
                runs(function () {
                    expect($.fn.scrollTo).toHaveBeenCalled();
                });
            });
        });

        xdescribe('scrollCaption', function () {
            beforeEach(function () {
                runs(function () {
                    state = jasmine.initializePlayer();
                });

                waitsFor(function () {
                    return state.videoCaption.rendered;
                }, 'Captions are not rendered', WAIT_TIMEOUT);
            });

            describe('when frozen', function () {
                it('does not scroll the caption', function () {
                    runs(function () {
                        state.videoCaption.frozen = true;
                        $('.subtitles li[data-index=1]').addClass('current');
                        state.videoCaption.scrollCaption();
                        expect($.fn.scrollTo).not.toHaveBeenCalled();
                    });
                });
            });

            describe('when not frozen', function () {
                beforeEach(function () {
                    runs(function () {
                        state.videoCaption.frozen = false;
                    });
                });

                describe('when there is no current caption', function () {
                    it('does not scroll the caption', function () {
                        runs(function () {
                            state.videoCaption.scrollCaption();
                            expect($.fn.scrollTo).not.toHaveBeenCalled();
                        });
                    });
                });

                describe('when there is a current caption', function () {
                    it('scroll to current caption', function () {
                        runs(function () {
                            $('.subtitles li[data-index=1]').addClass('current');
                            state.videoCaption.scrollCaption();
                            expect($.fn.scrollTo).toHaveBeenCalled();
                        });
                    });
                });
            });
        });

        xdescribe('seekPlayer', function () {
            beforeEach(function () {
                runs(function () {
                    state = jasmine.initializePlayer();
                });

                waitsFor(function () {
                    var duration = state.videoPlayer.duration(),
                        isRendered = state.videoCaption.rendered;

                    return isRendered && duration;
                }, 'Captions are not rendered', WAIT_TIMEOUT);
            });

            describe('when the video speed is 1.0x', function () {
                it('trigger seek event with the correct time', function () {
                    runs(function () {
                        state.videoSpeedControl.currentSpeed = '1.0';
                        $('.subtitles li[data-start="14910"]').trigger('click');
                        expect(state.videoPlayer.currentTime).toEqual(14.91);
                    });
                });
            });

            describe('when the video speed is not 1.0x', function () {
                it('trigger seek event with the correct time', function () {
                    runs(function () {
                        state.videoSpeedControl.currentSpeed = '0.75';
                        $('.subtitles li[data-start="14910"]').trigger('click');
                        expect(state.videoPlayer.currentTime).toEqual(14.91);
                    });
                });
            });

            describe('when the player type is Flash at speed 0.75x',
                function () {
                it('trigger seek event with the correct time', function () {
                    runs(function () {
                        state.videoSpeedControl.currentSpeed = '0.75';
                        state.currentPlayerMode = 'flash';
                        $('.subtitles li[data-start="14910"]').trigger('click');
                        expect(state.videoPlayer.currentTime).toEqual(15);
                    });
                });
            });
        });

        describe('toggle', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                $('.subtitles li[data-index=1]').addClass('current');
            });

            describe('when the caption is visible', function () {
                beforeEach(function () {
                    state.el.removeClass('closed');
                    state.videoCaption.toggle(jQuery.Event('click'));
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
                runs(function () {
                    state = jasmine.initializePlayer();
                });

                waitsFor(function () {
                    return state.videoCaption.rendered;
                }, 'Captions are not rendered', WAIT_TIMEOUT);
            });

            describe('when getting focus through TAB key', function () {
                beforeEach(function () {
                    runs(function () {
                        state.videoCaption.isMouseFocus = false;
                        $('.subtitles li[data-index=0]').trigger(
                            jQuery.Event('focus')
                        );
                    });
                });

                it('shows an outline around the caption', function () {
                    runs(function () {
                        expect($('.subtitles li[data-index=0]'))
                            .toHaveClass('focused');
                    });
                });

                it('has automatic scrolling disabled', function () {
                    runs(function () {
                        expect(state.videoCaption.autoScrolling).toBe(false);
                    });
                });
            });

            describe('when loosing focus through TAB key', function () {
                beforeEach(function () {
                    runs(function () {
                        $('.subtitles li[data-index=0]').trigger(
                            jQuery.Event('blur')
                        );
                    });
                });

                it('does not show an outline around the caption', function () {
                    runs(function () {
                        expect($('.subtitles li[data-index=0]'))
                            .not.toHaveClass('focused');
                    });
                });

                it('has automatic scrolling enabled', function () {
                    runs(function () {
                        expect(state.videoCaption.autoScrolling).toBe(true);
                    });
                });
            });

            describe(
                'when same caption gets the focus through mouse after ' +
                'having focus through TAB key',
                function () {

                beforeEach(function () {
                    runs(function () {
                        state.videoCaption.isMouseFocus = false;
                        $('.subtitles li[data-index=0]')
                            .trigger(jQuery.Event('focus'));
                        $('.subtitles li[data-index=0]')
                            .trigger(jQuery.Event('mousedown'));
                    });
                });

                it('does not show an outline around it', function () {
                    runs(function () {
                        expect($('.subtitles li[data-index=0]'))
                            .not.toHaveClass('focused');
                    });
                });

                it('has automatic scrolling enabled', function () {
                    runs(function () {
                        expect(state.videoCaption.autoScrolling).toBe(true);
                    });
                });
            });

            describe(
                'when a second caption gets focus through mouse after ' +
                'first had focus through TAB key',
                function () {

                var subDataLiIdx__0, subDataLiIdx__1;

                beforeEach(function () {
                    runs(function () {
                        subDataLiIdx__0 = $('.subtitles li[data-index=0]');
                        subDataLiIdx__1 = $('.subtitles li[data-index=1]');

                        state.videoCaption.isMouseFocus = false;

                        subDataLiIdx__0.trigger(jQuery.Event('focus'));
                        subDataLiIdx__0.trigger(jQuery.Event('blur'));

                        state.videoCaption.isMouseFocus = true;

                        subDataLiIdx__1.trigger(jQuery.Event('mousedown'));
                    });
                });

                it('does not show an outline around the first', function () {
                    runs(function () {
                        expect(subDataLiIdx__0).not.toHaveClass('focused');
                    });
                });

                it('does not show an outline around the second', function () {
                    runs(function () {
                        expect(subDataLiIdx__1).not.toHaveClass('focused');
                    });
                });

                it('has automatic scrolling enabled', function () {
                    runs(function () {
                        expect(state.videoCaption.autoScrolling).toBe(true);
                    });
                });
            });
        });
    });

}).call(this);
