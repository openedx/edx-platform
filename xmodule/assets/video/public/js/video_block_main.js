// Import required modules and dependencies
import $ from 'jquery';
import _ from 'underscore';
import {VideoStorage} from './video_storage';
import {VideoPoster} from './poster';
import {VideoTranscriptDownloadHandler} from './video_accessible_menu';
import {VideoSkipControl} from './skip_control';
import {VideoPlayPlaceholder} from './play_placeholder';
import {VideoPlaySkipControl} from './play_skip_control';
import {VideoPlayPauseControl} from './play_pause_control';


// TODO: Uncomment the imports
// import { initialize } from './initialize'; // Assuming this function is imported
// import {
//     FocusGrabber,
//     VideoControl,
//     VideoProgressSlider,
//     VideoSpeedControl,
//     VideoVolumeControl,
//     VideoQualityControl,
//     VideoFullScreen,
//     VideoCaption,
//     VideoCommands,
//     VideoContextMenu,
//     VideoSaveStatePlugin,
//     VideoEventsPlugin,
//     VideoCompletionHandler,
//     VideoTranscriptFeedback,
//     VideoAutoAdvanceControl,
//     VideoEventsBumperPlugin,
//     VideoSocialSharing,
//     VideoBumper,
// } from './video_modules'; // Assuming all necessary modules are grouped here

// Stub gettext if the runtime doesn't provide it
if (typeof window.gettext === 'undefined') {
    window.gettext = function (text) {
        return text;
    };
}


'use strict';

console.log('In video_block_main.js file');

(function () {
    var youtubeXhr = null;
    var oldVideo = window.Video;

    window.Video = function (runtime, element) {
        console.log('In Video initialize method');

        const el = $(element).find('.video');
        const id = el.attr('id').replace(/video_/, '');
        const storage = new VideoStorage('VideoState', id);
        const bumperMetadata = el.data('bumper-metadata');
        const autoAdvanceEnabled = el.data('autoadvance-enabled') === 'True';

        const mainVideoModules = [
            //     FocusGrabber,
            //     VideoControl,
            VideoPlayPlaceholder,
            VideoPlayPauseControl,
            //     VideoProgressSlider,
            //     VideoSpeedControl,
            //     VideoVolumeControl,
            //     VideoQualityControl,
            //     VideoFullScreen,
            //     VideoCaption,
            //     VideoCommands,
            //     VideoContextMenu,
            //     VideoSaveStatePlugin,
            //     VideoEventsPlugin,
            //     VideoCompletionHandler,
            //     VideoTranscriptFeedback,
            // ].concat(autoAdvanceEnabled ? [VideoAutoAdvanceControl] : []);
        ]

        const bumperVideoModules = [
            // VideoControl,
            VideoPlaySkipControl,
            VideoSkipControl,
            // VideoVolumeControl,
            // VideoCaption,
            // VideoCommands,
            // VideoSaveStatePlugin,
            // VideoTranscriptFeedback,
            // VideoEventsBumperPlugin,
            // VideoCompletionHandler,
        ];

        const state = {
            el: el,
            id: id,
            metadata: el.data('metadata'),
            storage: storage,
            options: {},
            youtubeXhr: youtubeXhr,
            modules: mainVideoModules,
        };

        const getBumperState = (metadata) => {
            return $.extend(true, {
                el: el,
                id: id,
                storage: storage,
                options: {SaveStatePlugin: {events: ['language_menu:change']}},
                youtubeXhr: youtubeXhr,
                modules: bumperVideoModules,
            }, {metadata: metadata});
        };

        const player = (innerState) => {
            return () => {
                _.extend(innerState.metadata, {autoplay: true, focusFirstControl: true});
                // TODO: Uncomment following initialize method calling
                // initialize(innerState, element);
            };
        };

        VideoTranscriptDownloadHandler(el, {
            storage: storage,
            saveStateUrl: state.metadata.saveStateUrl,
        });

        // VideoSocialSharing(el);

        if (bumperMetadata) {
            VideoPoster(el, {
                poster: el.data('poster'),
                onClick: _.once(function () {
                    const mainVideoPlayer = player(state);

                    if (storage.getItem('isBumperShown')) {
                        mainVideoPlayer();
                    } else {
                        const bumperState = getBumperState(bumperMetadata);
                        const bumper = new VideoBumper(player(bumperState), bumperState);

                        state.bumperState = bumperState;

                        bumper.getPromise().then(() => {
                            delete state.bumperState;
                            mainVideoPlayer();
                        });
                    }
                }),
            });
        } else {
            // TODO: Uncomment following initialize method calling
            // initialize(state, element);
        }

        if (!youtubeXhr) {
            youtubeXhr = state.youtubeXhr;
        }

        el.data('video-player-state', state);
        const onSequenceChange = () => {
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

    window.Video.clearYoutubeXhr = function () {
        youtubeXhr = null;
    };

    // TODO: Uncomment following initialize related code
    // window.Video.loadYouTubeIFrameAPI = initialize.prototype.loadYouTubeIFrameAPI;

    // Invoke the mock Video constructor so that the elements stored within it can be processed by the real
    // `window.Video` constructor.
    // TODO: Un comment following
    // oldVideo(null, true);

}());
