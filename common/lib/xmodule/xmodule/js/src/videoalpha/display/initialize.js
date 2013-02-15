(function (requirejs, require, define) {

// Initialize module.
define(
'videoalpha/display/initialize.js',
['videoalpha/display/bind.js'],
function (bind) {

    // Initialize() function - what this module "exports".
    return function (state, element) {
        // Functions which will be accessible via 'state' object.
        makeFunctionsPublic(state);

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

        // TODO: Check after refactoring whether this can be removed.
        state.el.addClass('video-load-complete');

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

        // Launch embedding of actual video content, or set it up so that it will be done as soon as the
        // appropriate video player (YouTube or stand alone HTML5) is loaded, and can handle embedding.
        if (
            ((state.videoType === 'youtube') && (window.YT) && (window.YT.Player)) ||
            ((state.videoType === 'html5') && (window.HTML5Video) && (window.HTML5Video.Player))
        ) {
            embed(state);
        } else {
            if (state.videoType === 'youtube') {
                window.onYouTubePlayerAPIReady = function() {
                    embed(state);
                };
            } else if (state.videoType === 'html5') {
                window.onHTML5PlayerAPIReady = function() {
                    embed(state);
                };
            }
        }
    };

    // Private functions start here.

    function makeFunctionsPublic(state) {
        state.setSpeed = bind(setSpeed, state);
        state.youtubeId = bind(youtubeId, state);
        state.getDuration = bind(getDuration, state);
        state.log = bind(log, state);
    }

    function parseYoutubeStreams(state, youtubeStreams) {
        if ((typeof youtubeStreams !== 'string') || (youtubeStreams.length === 0)) {
            return false;
        }

        state.videos = {};

        $.each(youtubeStreams.split(/,/), function(index, video) {
            var speed;

            video = video.split(/:/);
            speed = parseFloat(video[0]).toFixed(2).replace(/\.00$/, ".0");

            state.videos[speed] = video[1];
        });

        return true;
    }

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

    function fetchMetadata(state) {
        state.metadata = {};

        $.each(state.videos, function (speed, url) {
            $.get('https://gdata.youtube.com/feeds/api/videos/' + url + '?v=2&alt=jsonc', (function(data) {
                state.metadata[data.data.id] = data.data;
            }), 'jsonp');
        });
    }

    function parseSpeed(state) {
        state.speeds = ($.map(state.videos, function(url, speed) {
            return speed;
        })).sort();

        state.setSpeed($.cookie('video_speed'));
    }

    function embed(state) { }

    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().

    function setSpeed(newSpeed) {
        if (this.speeds.indexOf(newSpeed) !== -1) {
            this.speed = newSpeed;

            $.cookie('video_speed', '' + newSpeed, {
                expires: 3650,
                path: '/'
            });
        } else {
            this.speed = '1.0';
        }
    }

    function youtubeId(speed) {
        return this.videos[speed || this.speed];
    }

    function getDuration() {
        return this.metadata[this.youtubeId()].duration;
    }

    function log(eventName) {
        var logInfo;

        logInfo = {
            'id':          this.id,
            'code':        this.youtubeId(),
            'currentTime': this.player.currentTime,
            'speed':       this.speed
        };

        if (this.videoType === 'youtube') {
            logInfo.code = this.youtubeId();
        } else {
            if (this.videoType === 'html5') {
                logInfo.code = 'html5';
            }
        }

        Logger.log(eventName, logInfo);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
