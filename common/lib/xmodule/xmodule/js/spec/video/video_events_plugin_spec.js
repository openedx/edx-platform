(function (undefined) {
    'use strict';
    describe('VideoPlayer Events plugin', function () {
        var state, oldOTBD;

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice')
                .andReturn(null);

            jasmine.stubRequests();
            state = jasmine.initializePlayer();
            spyOn(Logger, 'log');
            spyOn(state.videoEventsPlugin, 'getCurrentTime').andReturn(10);
        });

        afterEach(function () {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            state.storage.clear();
            if (state.videoPlayer) {
                state.videoPlayer.destroy();
            }
        });

        it('can emit "load_video" event', function () {
            state.el.trigger('ready');
            expect(Logger.log).toHaveBeenCalledWith('load_video', {
                id: 'id',
                code: 'html5'
            });
        });

        it('can emit "play_video" event', function () {
            state.el.trigger('play');
            expect(Logger.log).toHaveBeenCalledWith('play_video', {
                id: 'id',
                code: 'html5',
                currentTime: 10
            });
        });

        it('can emit "pause_video" event', function () {
            state.el.trigger('pause');
            expect(Logger.log).toHaveBeenCalledWith('pause_video', {
                id: 'id',
                code: 'html5',
                currentTime: 10
            });
        });

        it('can emit "speed_change_video" event', function () {
            state.el.trigger('speedchange', ['2.0', '1.0']);
            expect(Logger.log).toHaveBeenCalledWith('speed_change_video', {
                id: 'id',
                code: 'html5',
                current_time: 10,
                old_speed: '1.0',
                new_speed: '2.0'
            });
        });

        it('can emit "seek_video" event', function () {
            state.el.trigger('seek', [1, 0, 'any']);
            expect(Logger.log).toHaveBeenCalledWith('seek_video', {
                id: 'id',
                code: 'html5',
                old_time: 0,
                new_time: 1,
                type: 'any'
            });
        });

        it('can emit "stop_video" event', function () {
            state.el.trigger('ended');
            expect(Logger.log).toHaveBeenCalledWith('stop_video', {
                id: 'id',
                code: 'html5',
                currentTime: 10
            });

            Logger.log.reset();
            state.el.trigger('stop');
            expect(Logger.log).toHaveBeenCalledWith('stop_video', {
                id: 'id',
                code: 'html5',
                currentTime: 10
            });
        });

        it('can emit "skip_video" event', function () {
            state.el.trigger('skip', [false]);
            expect(Logger.log).toHaveBeenCalledWith('skip_video', {
                id: 'id',
                code: 'html5',
                currentTime: 10
            });
        });

        it('can emit "do_not_show_again_video" event', function () {
            state.el.trigger('skip', [true]);
            expect(Logger.log).toHaveBeenCalledWith('do_not_show_again_video', {
                id: 'id',
                code: 'html5',
                currentTime: 10
            });
        });

        it('can emit "video_show_cc_menu" event', function () {
            state.el.trigger('language_menu:show');
            expect(Logger.log).toHaveBeenCalledWith('video_show_cc_menu', {
                id: 'id',
                code: 'html5'
            });
        });

        it('can emit "video_hide_cc_menu" event', function () {
            state.el.trigger('language_menu:hide');
            expect(Logger.log).toHaveBeenCalledWith('video_hide_cc_menu', {
                id: 'id',
                code: 'html5'
            });
        });

        it('can emit "show_transcript" event', function () {
            state.el.trigger('captions:show');
            expect(Logger.log).toHaveBeenCalledWith('show_transcript', {
                id: 'id',
                code: 'html5',
                current_time: 10
            });
        });

        it('can emit "hide_transcript" event', function () {
            state.el.trigger('captions:hide');
            expect(Logger.log).toHaveBeenCalledWith('hide_transcript', {
                id: 'id',
                code: 'html5',
                current_time: 10
            });
        });

        it('can destroy itself', function () {
            var plugin = state.videoEventsPlugin;
            spyOn($.fn, 'off').andCallThrough();
            state.videoEventsPlugin.destroy();
            expect(state.videoEventsPlugin).toBeUndefined();
            expect($.fn.off).toHaveBeenCalledWith({
                'ready': plugin.onReady,
                'play': plugin.onPlay,
                'pause': plugin.onPause,
                'ended stop': plugin.onEnded,
                'seek': plugin.onSeek,
                'skip': plugin.onSkip,
                'speedchange': plugin.onSpeedChange,
                'language_menu:show': plugin.onShowLanguageMenu,
                'language_menu:hide': plugin.onHideLanguageMenu,
                'captions:show': plugin.onShowCaptions,
                'captions:hide': plugin.onHideCaptions,
                'destroy': plugin.destroy
            });
        });
    });

}).call(this);
