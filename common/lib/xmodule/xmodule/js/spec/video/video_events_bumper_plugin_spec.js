(function(undefined) {
    'use strict';
    describe('VideoPlayer Events Bumper plugin', function() {
        var Logger = window.Logger;
        var state, oldOTBD;

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice')
                .and.returnValue(null);

            state = jasmine.initializePlayer('video_with_bumper.html');
            spyOn(Logger, 'log');
            $('.poster .btn-play').click();
            spyOn(state.bumperState.videoEventsBumperPlugin, 'getCurrentTime').and.returnValue(10);
            spyOn(state.bumperState.videoEventsBumperPlugin, 'getDuration').and.returnValue(20);
        });

        afterEach(function() {
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
            state.storage.clear();
            if (state.bumperState && state.bumperState.videoPlayer) {
                state.bumperState.videoPlayer.destroy();
            }
            if (state.videoPlayer) {
                state.videoPlayer.destroy();
            }
        });

        it('can emit "edx.video.bumper.loaded" event', function() {
            state.el.trigger('ready');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.loaded', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.played" event', function() {
            state.el.trigger('play');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.played', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.stopped" event', function() {
            state.el.trigger('ended');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.stopped', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });

            Logger.log.calls.reset();
            state.el.trigger('stop');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.stopped', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.skipped" event', function() {
            state.el.trigger('skip', [false]);
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.skipped', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.dismissed" event', function() {
            state.el.trigger('skip', [true]);
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.dismissed', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.transcript.menu.shown" event', function() {
            state.el.trigger('language_menu:show');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.transcript.menu.shown', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.transcript.menu.hidden" event', function() {
            state.el.trigger('language_menu:hide');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.transcript.menu.hidden', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.transcript.shown" event', function() {
            state.el.trigger('captions:show');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.transcript.shown', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });
        });

        it('can emit "edx.video.bumper.transcript.hidden" event', function() {
            state.el.trigger('captions:hide');
            expect(Logger.log).toHaveBeenCalledWith('edx.video.bumper.transcript.hidden', {
                host_component_id: 'id',
                bumper_id: '/base/fixtures/test.mp4',
                code: 'html5',
                currentTime: 10,
                duration: 20
            });
        });

        it('can destroy itself', function() {
            var plugin = state.bumperState.videoEventsBumperPlugin;
            spyOn($.fn, 'off').and.callThrough();
            plugin.destroy();
            expect(state.bumperState.videoEventsBumperPlugin).toBeUndefined();
            expect($.fn.off).toHaveBeenCalledWith({
                'ready': plugin.onReady,
                'play': plugin.onPlay,
                'ended stop': plugin.onEnded,
                'skip': plugin.onSkip,
                'language_menu:show': plugin.onShowLanguageMenu,
                'language_menu:hide': plugin.onHideLanguageMenu,
                'captions:show': plugin.onShowCaptions,
                'captions:hide': plugin.onHideCaptions,
                'destroy': plugin.destroy
            });
        });
    });
}).call(this);
