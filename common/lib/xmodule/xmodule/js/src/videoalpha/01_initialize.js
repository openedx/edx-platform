/**
 * @file Initialize module works with the JSON config, and sets up various settings, parameters,
 * variables. After all setup actions are performed, it invokes the video player to play the
 * specified video. This module must be invoked first. It provides several functions which do not
 * fit in with other modules.
 *
 * @external VideoPlayer
 *
 * @module Initialize
 */

(function (requirejs, require, define) {

define(
'videoalpha/01_initialize.js',
['videoalpha/03_video_player.js'],
function (VideoPlayer) {

    /**
     * @function
     *
     * Initialize module exports this function.
     *
     * @param {Object} state A place for all properties, and methods of Video Alpha.
     * @param {DOM element} element Container of the entire Video Alpha DOM element.
     */
    return function (state, element) {
        _makeFunctionsPublic(state);
        _initialize(state, element);
        _renderElements(state);
    };

    // ***************************************************************
    // Private functions start here. Private functions start with underscore.
    // ***************************************************************

    /**
     * @function _makeFunctionsPublic
     *
     * Functions which will be accessible via 'state' object. When called, these functions will get the 'state'
     * object as a context.
     *
     * @param {Object} state A place for all properties, and methods of Video Alpha.
     */
    function _makeFunctionsPublic(state) {
        state.setSpeed    = _.bind(setSpeed, state);
        state.youtubeId   = _.bind(youtubeId, state);
        state.getDuration = _.bind(getDuration, state);
        state.trigger     = _.bind(trigger, state);

        // Old private functions. Now also public so that can be
        // tested by Jasmine.

        state.parseSpeed = _.bind(parseSpeed, state);
        state.fetchMetadata = _.bind(fetchMetadata, state);
        state.parseYoutubeStreams = _.bind(parseYoutubeStreams, state);
        state.parseVideoSources = _.bind(parseVideoSources, state);
    }

    // function _initialize(element)
    // The function set initial configuration and preparation.

    function _initialize(state, element) {
        // This is used in places where we instead would have to check if an element has a CSS class 'fullscreen'.
        state.isFullScreen = false;

        // The parent element of the video, and the ID.
        state.el = $(element).find('.videoalpha');
        state.id = state.el.attr('id').replace(/video_/, '');

        // We store all settings passed to us by the server in one place. These are "read only", so don't
        // modify them. All variable content lives in 'state' object.
        state.config = {
            element: element,

            start:              state.el.data('start'),
            end:                state.el.data('end'),

            caption_data_dir:   state.el.data('caption-data-dir'),
            caption_asset_path: state.el.data('caption-asset-path'),
            show_captions:      (state.el.data('show-captions').toString().toLowerCase() === 'true'),
            youtubeStreams:     state.el.data('streams'),

            sub:                state.el.data('sub'),
            mp4Source:          state.el.data('mp4-source'),
            webmSource:         state.el.data('webm-source'),
            oggSource:          state.el.data('ogg-source'),

            fadeOutTimeout:     1400,

            availableQualities: ['hd720', 'hd1080', 'highres'],

            qTipConfig: {
                position: {
                    my: 'top right',
                    at: 'top center'
                }
            },

            inCms:              state.el.data('in-studio')
        };

        if (!(_parseYouTubeIDs(state))) {
            // If we do not have YouTube ID's, try parsing HTML5 video sources.
            _prepareHTML5Video(state);
        }

        _configureCaptions(state);
        _setPlayerMode(state);

        // Possible value are: 'visible', 'hiding', and 'invisible'.
        state.controlState = 'visible';
        state.controlHideTimeout = null;
        state.captionState = 'visible';
        state.captionHideTimeout = null;
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        // Launch embedding of actual video content, or set it up so that it will be done as soon as the
        // appropriate video player (YouTube or stand alone HTML5) is loaded, and can handle embedding.
        //
        // Note that the loading of stand alone HTML5 player API is handled by Require JS. At the time
        // when we reach this code, the stand alone HTML5 player is already loaded, so no further testing
        // in that case is required.
        var onPlayerReadyFunc;
        if (
            ((state.videoType === 'youtube') && (window.YT) && (window.YT.Player)) ||
            (state.videoType === 'html5')
        ) {
            VideoPlayer(state);
        } else {
            onPlayerReadyFunc = (state.videoType === 'youtube') ? 'onYouTubePlayerAPIReady' : 'onHTML5PlayerAPIReady';
            window[onPlayerReadyFunc] = _.bind(VideoPlayer, window, state);
        }
    }

    // function _configureCaptions(state)
    //     Configure displaying of captions.
    //
    //     Option
    //         this.config.show_captions = true | false
    //
    //     defines whether to turn off/on the captions altogether. User will not have the ability to turn them on/off.
    //
    //     Option
    //          this.hide_captions = true | false
    //
    //     represents the user's choice of having the subtitles shown or hidden. This choice is stored in cookies.
    function _configureCaptions(state) {
        if (state.config.show_captions) {
            state.hide_captions = ($.cookie('hide_captions') === 'true');
        } else {
            state.hide_captions = true;

            $.cookie('hide_captions', state.hide_captions, {
                expires: 3650,
                path: '/'
            });

            state.el.addClass('closed');
        }
    }

    // function _setPlayerMode(state)
    //     By default we will be forcing HTML5 player mode. Only in the case when, after initializtion, we will
    //     get one available playback rate, we will change to Flash player mode. There is a need to store this
    //     setting in cookies because otherwise we will have to change from HTML5 to Flash on every page load
    //     in a browser that doesn't fully support HTML5. When we have this setting in cookies, we can select
    //     the proper mode from the start (not having to change mode later on).
    function _setPlayerMode(state) {
        (function (currentPlayerMode) {
            if ((currentPlayerMode === 'html5') || (currentPlayerMode === 'flash')) {
                state.currentPlayerMode = currentPlayerMode;
            } else {
                $.cookie('current_player_mode', 'html5', {
                    expires: 3650,
                    path: '/'
                });
                state.currentPlayerMode = 'html5';
            }
        }($.cookie('current_player_mode')));
    }

    // function _parseYouTubeIDs(state)
    //     The function parse YouTube stream ID's.
    //     @return
    //         false: We don't have YouTube video IDs to work with; most likely we have HTML5 video sources.
    //         true: Parsing of YouTube video IDs went OK, and we can proceed onwards to play YouTube videos.
    function _parseYouTubeIDs(state) {
        if (state.parseYoutubeStreams(state.config.youtubeStreams)) {
            state.videoType = 'youtube';

            state.fetchMetadata();
            state.parseSpeed();
            return true;
        }
        return false;
    }

    // function _prepareHTML5Video(state)
    // The function prepare HTML5 video, parse HTML5
    // video sources etc.
    function _prepareHTML5Video(state) {
        state.videoType = 'html5';

        state.parseVideoSources(
            {
                mp4: state.config.mp4Source,
                webm: state.config.webmSource,
                ogg: state.config.oggSource
            }
        );

        if (!state.config.sub || !state.config.sub.length) {
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

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

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
    function parseYoutubeStreams(youtubeStreams) {
        var _this;

        if (typeof youtubeStreams === 'undefined' || youtubeStreams.length === 0) {
            return false;
        }

        _this = this;
        this.videos = {};

        $.each(youtubeStreams.split(/,/), function(index, video) {
            var speed;

            video = video.split(/:/);
            speed = parseFloat(video[0]).toFixed(2).replace(/\.00$/, '.0');

            _this.videos[speed] = video[1];
        });

        return true;
    }

    // function parseVideoSources(, mp4Source, webmSource, oggSource)
    //
    //     Take the HTML5 sources (URLs of videos), and make them available explictly for each type
    //     of video format (mp4, webm, ogg).
    function parseVideoSources(sources) {
        var _this = this;

        this.html5Sources = {
            mp4: null,
            webm: null,
            ogg: null
        };

        $.each(sources, function (name, source) {
            if (source && source.length) {
                _this.html5Sources[name] = source;
            }
        });
    }

    // function fetchMetadata()
    //
    //     When dealing with YouTube videos, we must fetch meta data that has certain key facts
    //     not available while the video is loading. For example the length of the video can be
    //     determined from the meta data.
    function fetchMetadata() {
        var _this = this;

        this.metadata = {};

        $.each(this.videos, function (speed, url) {
            $.get('https://gdata.youtube.com/feeds/api/videos/' + url + '?v=2&alt=jsonc', (function(data) {
                _this.metadata[data.data.id] = data.data;
            }), 'jsonp');
        });
    }

    // function parseSpeed()
    //
    //     Create a separate array of available speeds.
    function parseSpeed() {
        this.speeds = ($.map(this.videos, function(url, speed) {
            return speed;
        })).sort();

        this.setSpeed($.cookie('video_speed'));
    }

    function setSpeed(newSpeed, updateCookie) {
        if (_.indexOf(this.speeds, newSpeed) !== -1) {
            this.speed = newSpeed;
        } else {
            this.speed = '1.0';
        }

        if (updateCookie) {
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
     * The trigger() function will assume that the @objChain is a complete chain with a method
     * (function) at the end. It will call this function. So for example, when trigger() is
     * called like so:
     *
     *     state.trigger('videoPlayer.pause', {'param1': 10});
     *
     * Then trigger() will execute:
     *
     *     state.videoPlayer.pause({'param1': 10});
     */
    function trigger(objChain, extraParameters) {
        var i, tmpObj, chain;

        // Remember that 'this' is the 'state' object.
        tmpObj = this;
        chain = objChain.split('.');

        // At the end of the loop the variable 'tmpObj' will either be the correct
        // object/function to trigger/invoke. If the 'chain' chain of object is
        // incorrect (one of the link is non-existent), then the loop will immediately
        // exit.
        while (chain.length) {
            i = chain.shift();

            if (tmpObj.hasOwnProperty(i)) {
                tmpObj = tmpObj[i];
            } else {
                // An incorrect object chain was specified.

                return false;
            }
        }

        tmpObj(extraParameters);

        return true;
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
