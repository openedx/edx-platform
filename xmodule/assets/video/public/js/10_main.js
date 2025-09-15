/* globals _ */
/* RequireJS */
(function(require, $) {
    'use strict';

    // In the case when the Video constructor will be called before RequireJS finishes loading all of the Video
    // dependencies, we will have a mock function that will collect all the elements that must be initialized as
    // Video elements.
    //
    // Once RequireJS will load all of the necessary dependencies, main code will invoke the mock function with
    // the second parameter set to truthy value. This will trigger the actual Video constructor on all elements
    // that are stored in a temporary list.
    window.Video = (function() {
        // Temporary storage place for elements that must be initialized as Video elements.
        var tempCallStack = [];

        return function(element, processTempCallStack) {
            // If mock function was called with second parameter set to truthy value, we invoke the real `window.Video`
            // on all the stored elements so far.
            if (processTempCallStack) {
                $.each(tempCallStack, function(index, el) {
                    // By now, `window.Video` is the real constructor.
                    window.Video(el);
                });

                return null;
            }

            // If normal call to `window.Video` constructor, store the element for later initializing.
            tempCallStack.push(element);

            // Real Video constructor returns the `state` object. The mock function will return an empty object.
            return {};
        };
    }());

    // Main module.
    require(
        /* End RequireJS */
    /* Webpack
    define(
    /* End Webpack */
        [
            'video/00_video_storage.js',
            'video/01_initialize.js',
            'video/025_focus_grabber.js',
            'video/035_video_accessible_menu.js',
            'video/04_video_control.js',
            'video/04_video_full_screen.js',
            'video/05_video_quality_control.js',
            'video/06_video_progress_slider.js',
            'video/07_video_volume_control.js',
            'video/08_video_speed_control.js',
            'video/08_video_auto_advance_control.js',
            'video/09_video_caption.js',
            'video/09_play_placeholder.js',
            'video/09_play_pause_control.js',
            'video/09_play_skip_control.js',
            'video/09_skip_control.js',
            'video/09_bumper.js',
            'video/09_save_state_plugin.js',
            'video/09_events_plugin.js',
            'video/09_events_bumper_plugin.js',
            'video/09_poster.js',
            'video/09_completion.js',
            'video/10_commands.js',
            'video/095_video_context_menu.js',
            'video/036_video_social_sharing.js',
            'video/037_video_transcript_feedback.js'
        ],
        function(
            VideoStorage, initialize, FocusGrabber, VideoAccessibleMenu, VideoControl, VideoFullScreen,
            VideoQualityControl, VideoProgressSlider, VideoVolumeControl, VideoSpeedControl, VideoAutoAdvanceControl,
            VideoCaption, VideoPlayPlaceholder, VideoPlayPauseControl, VideoPlaySkipControl, VideoSkipControl,
            VideoBumper, VideoSaveStatePlugin, VideoEventsPlugin, VideoEventsBumperPlugin, VideoPoster,
            VideoCompletionHandler, VideoCommands, VideoContextMenu, VideoSocialSharing, VideoTranscriptFeedback
        ) {
            /* RequireJS */
            var youtubeXhr = null,
                oldVideo = window.Video;
            /* End RequireJS */
            /* Webpack
            var youtubeXhr = null;
            /* End Webpack */

            window.Video = function(element) {
                var el = $(element).find('.video'),
                    id = el.attr('id').replace(/video_/, ''),
                    storage = VideoStorage('VideoState', id),
                    bumperMetadata = el.data('bumper-metadata'),
                    autoAdvanceEnabled = el.data('autoadvance-enabled') === 'True',
                    mainVideoModules = [
                        FocusGrabber, VideoControl, VideoPlayPlaceholder,
                        VideoPlayPauseControl, VideoProgressSlider, VideoSpeedControl,
                        VideoVolumeControl, VideoQualityControl, VideoFullScreen, VideoCaption, VideoCommands,
                        VideoContextMenu, VideoSaveStatePlugin, VideoEventsPlugin, VideoCompletionHandler, VideoTranscriptFeedback
                    ].concat(autoAdvanceEnabled ? [VideoAutoAdvanceControl] : []),
                    bumperVideoModules = [VideoControl, VideoPlaySkipControl, VideoSkipControl,
                        VideoVolumeControl, VideoCaption, VideoCommands, VideoSaveStatePlugin, VideoTranscriptFeedback,
                        VideoEventsBumperPlugin, VideoCompletionHandler],
                    state = {
                        el: el,
                        id: id,
                        metadata: el.data('metadata'),
                        storage: storage,
                        options: {},
                        youtubeXhr: youtubeXhr,
                        modules: mainVideoModules
                    };

                var getBumperState = function(metadata) {
                    var bumperState = $.extend(true, {
                        el: el,
                        id: id,
                        storage: storage,
                        options: {},
                        youtubeXhr: youtubeXhr
                    }, {metadata: metadata});

                    bumperState.modules = bumperVideoModules;
                    bumperState.options = {
                        SaveStatePlugin: {events: ['language_menu:change']}
                    };
                    return bumperState;
                };

                var player = function(innerState) {
                    return function() {
                        _.extend(innerState.metadata, {autoplay: true, focusFirstControl: true});
                        initialize(innerState, element);
                    };
                };
                var onSequenceChange;

                VideoAccessibleMenu(el, {
                    storage: storage,
                    saveStateUrl: state.metadata.saveStateUrl
                });

                VideoSocialSharing(el);

                if (bumperMetadata) {
                    VideoPoster(el, {
                        poster: el.data('poster'),
                        onClick: _.once(function() {
                            var mainVideoPlayer = player(state);
                            var bumper, bumperState;
                            if (storage.getItem('isBumperShown')) {
                                mainVideoPlayer();
                            } else {
                                bumperState = getBumperState(bumperMetadata);
                                bumper = new VideoBumper(player(bumperState), bumperState);
                                state.bumperState = bumperState;
                                bumper.getPromise().done(function() {
                                    delete state.bumperState;
                                    mainVideoPlayer();
                                });
                            }
                        })
                    });
                } else {
                    initialize(state, element);
                }

                if (!youtubeXhr) {
                    youtubeXhr = state.youtubeXhr;
                }

                el.data('video-player-state', state);
                onSequenceChange = function() {
                    if (state && state.videoPlayer) {
                        state.videoPlayer.destroy();
                    }
                    $('.sequence').off('sequence:change', onSequenceChange);
                };
                $('.sequence').on('sequence:change', onSequenceChange);

                // Because the 'state' object is only available inside this closure, we will also make it available to
                // the caller by returning it. This is necessary so that we can test Video with Jasmine.
                return state;
            };

            window.Video.clearYoutubeXhr = function() {
                youtubeXhr = null;
            };

            window.Video.loadYouTubeIFrameAPI = initialize.prototype.loadYouTubeIFrameAPI;

            /* RequireJS */
            // Invoke the mock Video constructor so that the elements stored within it can be processed by the real
            // `window.Video` constructor.
            oldVideo(null, true);
            /* End RequireJS */
        }
    );
/* RequireJS */
}(window.RequireJS.require, window.jQuery));
/* End RequireJS */
