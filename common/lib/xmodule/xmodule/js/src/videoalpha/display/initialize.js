(function (requirejs, require, define) {

// Initialize module.
define(
'videoalpha/display/initialize.js',
[
    'videoalpha/display/bind.js',
    'videoalpha/display/video_player.js'
],
function (bind, VideoPlayer) {

    // Initialize() function - what this module "exports".
    return function (state, element) {
        makeFunctionsPublic(state);
        renderElements(state, element);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function makeFunctionsPublic(state) {
        state.setSpeed    = bind(setSpeed, state);
        state.youtubeId   = bind(youtubeId, state);
        state.getDuration = bind(getDuration, state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state, element) {
        // The parent element of the video, and the ID.
        state.el = $(element).find('.video');
        state.id = state.el.attr('id').replace(/video_/, '');

        // We store all settings passed to us by the server in one place. These are "read only", so don't
        // modify them. All variable content lives in 'state' object.
        state.config = {
            'element': element,

            'start':              state.el.data('start'),
            'end':                state.el.data('end'),

            'caption_data_dir':   state.el.data('caption-data-dir'),
            'caption_asset_path': state.el.data('caption-asset-path'),
            'show_captions':      (state.el.data('show-captions').toString() === 'true'),

            'youtubeStreams':     state.el.data('streams'),

            'sub':                state.el.data('sub'),
            'mp4Source':          state.el.data('mp4-source'),
            'webmSource':         state.el.data('webm-source'),
            'oggSource':          state.el.data('ogg-source')
        };

        // Try to parse YouTube stream ID's. If
        if (parseYoutubeStreams(state, state.config.youtubeStreams) === true) {
            state.videoType = 'youtube';

            fetchMetadata(state);
            parseSpeed(state);
        }

        // If we do not have YouTube ID's, try parsing HTML5 video sources.
        else {
            state.videoType = 'html5';

            parseVideoSources(
                state,
                state.config.mp4Source,
                state.config.webmSource,
                state.config.oggSource
            );

            if ((typeof state.config.sub !== 'string') || (state.config.sub.length === 0)) {
                state.config.sub = '';
                state.config.show_captions = false;
            }

            state.speeds = ['0.75', '1.0', '1.25', '1.50'];
            state.videos = {
                '0.75': state.config.sub,
                '1.0':  state.config.sub,
                '1.25': state.config.sub,
                '1.5':  state.config.sub
            };

            state.setSpeed($.cookie('video_speed'));
        }

        // Configure displaying of captions.
        //
        // Option
        //
        //     state.config.show_captions = true | false
        //
        // defines whether to turn off/on the captions altogether. User will not have the ability to turn them on/off.
        //
        // Option
        //
        //     state.hide_captions = true | false
        //
        // represents the user's choice of having the subtitles shown or hidden. This choice is stored in cookies.
        if (state.config.show_captions === true) {
            state.hide_captions = ($.cookie('hide_captions') === 'true');
        } else {
            state.hide_captions = true;

            $.cookie('hide_captions', state.hide_captions, {
                expires: 3650,
                path: '/'
            });

            state.el.addClass('closed');
        }

        // By default we will be forcing HTML5 player mode. Only in the case when, after initializtion, we will
        // get one available playback rate, we will change to Flash player mode. There is a need to store this
        // setting in cookies because otherwise we will have to change from HTML5 to Flash on every page load
        // in a browser that doesn't fully support HTML5. When we have this setting in cookies, we can select
        // the proper mode from the start (not having to change mode later on).
        (function (currentPlayerMode) {
            if ((currentPlayerMode !== 'html5') && (currentPlayerMode !== 'flash')) {
                $.cookie('current_player_mode', 'html5', {
                    expires: 3650,
                    path: '/'
                });
                state.currentPlayerMode = 'html5';
            } else  {
                state.currentPlayerMode = currentPlayerMode;
            }
        }($.cookie('current_player_mode')));

        // Will be used by various components to register callbacks that can be then called by video core,
        // or other components.
        state.callbacks = {
            'videoPlayer': {
                'onPlay': [],
                'onPause': [],
                'onEnded': [],
                'onPlaybackQualityChange': [],
                'updatePlayTime': [],
                'onSpeedSetChange': []
            },
            'videoControl': {
                'togglePlaybackPlay': [],
                'togglePlaybackPause': [],
                'toggleFullScreen': []
            },
            'videoQualityControl': {
                'toggleQuality': []
            },
            'videoProgressSlider': {
                'onSlide': [],
                'onStop': []
            },
            'videoVolumeControl': {
                'onChange': []
            },
            'videoSpeedControl': {
                'changeVideoSpeed': []
            },
            'videoCaption': {
                'seekPlayer': []
            }
        };

        // Launch embedding of actual video content, or set it up so that it will be done as soon as the
        // appropriate video player (YouTube or stand alone HTML5) is loaded, and can handle embedding.
        //
        // Note that the loading of stand alone HTML5 player API is handled by Require JS. At the time
        // when we reach this code, the stand alone HTML5 player is already loaded, so no further testing
        // in that case is required.
        if (
            ((state.videoType === 'youtube') && (window.YT) && (window.YT.Player)) ||
            (state.videoType === 'html5')
        ) {
            embed(state);
        } else {
            if (state.videoType === 'youtube') {
                window.onYouTubePlayerAPIReady = function() {
                    embed(state);
                };
            } else { // if (state.videoType === 'html5') {
                window.onHTML5PlayerAPIReady = function() {
                    embed(state);
                };
            }
        }
    }

    // function parseYoutubeStreams(state, youtubeStreams)
    //
    //     Take a string in the form:
    //         "iCawTYPtehk:0.75,KgpclqP-LBA:1.0,9-2670d5nvU:1.5"
    //     parse it, and make it available via the 'state' object. If we are not given a string, or
    //     it's length is zero, then we return false.
    //
    //     @return
    //         false: We don't have YouTube video IDs to work with; most likely we have HTML5 video sources.
    //         true: Parsing of YouTube video IDs went OK, and we can proceed onwards to play YouTube videos.
    function parseYoutubeStreams(state, youtubeStreams) {
        if ((typeof youtubeStreams !== 'string') || (youtubeStreams.length === 0)) {
            return false;
        }

        state.videos = {};

        $.each(youtubeStreams.split(/,/), function(index, video) {
            var speed;

            video = video.split(/:/);
            speed = parseFloat(video[0]).toFixed(2).replace(/\.00$/, '.0');

            state.videos[speed] = video[1];
        });

        return true;
    }

    // function parseVideoSources(state, mp4Source, webmSource, oggSource)
    //
    //     Take the HTML5 sources (URLs of videos), and make them available explictly for each type
    //     of video format (mp4, webm, ogg).
    function parseVideoSources(state, mp4Source, webmSource, oggSource) {
        state.html5Sources = { 'mp4': null, 'webm': null, 'ogg': null };

        if ((typeof mp4Source === 'string') && (mp4Source.length > 0)) {
            state.html5Sources.mp4 = mp4Source;
        }
        if ((typeof webmSource === 'string') && (webmSource.length > 0)) {
            state.html5Sources.webm = webmSource;
        }
        if ((typeof oggSource === 'string') && (oggSource.length > 0)) {
            state.html5Sources.ogg = oggSource;
        }
    }

    // function fetchMetadata(state)
    //
    //     When dealing with YouTube videos, we must fetch meta data that has certain key facts
    //     not available while the video is loading. For example the length of the video can be
    //     determined from the meta data.
    function fetchMetadata(state) {
        state.metadata = {};

        $.each(state.videos, function (speed, url) {
            $.get('https://gdata.youtube.com/feeds/api/videos/' + url + '?v=2&alt=jsonc', (function(data) {
                state.metadata[data.data.id] = data.data;
            }), 'jsonp');
        });
    }

    // function parseSpeed(state)
    //
    //     Create a separate array of available speeds.
    function parseSpeed(state) {
        state.speeds = ($.map(state.videos, function(url, speed) {
            return speed;
        })).sort();

        state.setSpeed($.cookie('video_speed'));
    }

    // function embed(state)
    //
    //     This function is called when the current type of video player API becomes available.
    //     It instantiates the core video module.
    function embed(state) {
        VideoPlayer(state);
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function setSpeed(newSpeed, updateCookie) {
        if (this.speeds.indexOf(newSpeed) !== -1) {
            this.speed = newSpeed;
        } else {
            this.speed = '1.0';
        }

        if (updateCookie !== false) {
            $.cookie('video_speed', this.speed, {
                expires: 3650,
                path: '/'
            });
        }
    }

    function youtubeId(speed) {
        return this.videos[speed || this.speed];
    }

    function getDuration() {
        return this.metadata[this.youtubeId()].duration;
    }

     /*
     * Because jQuery events can be triggered on some jQuery object, we must make sure that
     * we don't trigger an event on an undefined object. For this we will have an in-between
     * method that will check for the existance of an object before triggering an event on it.
     *
     * @objChain is an array that contains the chain of properties on the 'state' object. For
     * example, if
     *
     *     objChain = ['videoPlayer', 'stopVideo'];
     *
     * then we will check for the existance of the
     *
     *     state.videoPlayer.stopVideo
     *
     * object, and, if found to be present, will trigger the specified event on this object.
     *
     * @eventName - the name of the event to trigger on the specified object.
     */
    function trigger(objChain, eventName, extraParameters) {
        var tmpObj;

        // Remember that 'this' is the 'state' object.
        tmpObj = this;

        getFinalObj(0);

        if (tmpObj === null) {
            return false;
        }

        tmpObj.trigger(eventName, extraParameters);

        return true;

        function getFinalObj(i) {
            if (objChain.length !== i) {
                if (tmpObj.hasOwnProperty(objChain[i]) === true) {
                    tmpObj = tmpObj[objChain[i]];
                    getFinalObj(i + 1);
                } else {
                    tmpObj = null;
                }
            }
        }
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
