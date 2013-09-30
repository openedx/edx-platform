/**
 * @file Initialize module works with the JSON config, and sets up various
 * settings, parameters, variables. After all setup actions are performed, it
 * invokes the video player to play the specified video. This module must be
 * invoked first. It provides several functions which do not fit in with other
 * modules.
 *
 * @external VideoPlayer
 *
 * @module Initialize
 */

(function (requirejs, require, define) {

define(
'video/01_initialize.js',
['video/03_video_player.js'],
function (VideoPlayer) {

    // window.console.log() is expected to be available. We do not support
    // browsers which lack this functionality.

    // The function gettext() is defined by a vendor library. If, however, it
    // is undefined, it is a simple wrapper. It is used to return a different
    // version of the string passed (translated string, etc.). In the basic
    // case, the original string is returned.
    if (typeof(window.gettext) == 'undefined') {
        window.gettext = function (s) {
            return s;
        };
    }

    /**
     * @function
     *
     * Initialize module exports this function.
     *
     * @param {object} state The object containg the state of the video player.
     *     All other modules, their parameters, public variables, etc. are
     *     available via this object.
     * @param {DOM element} element Container of the entire Video DOM element.
     */
    return function (state, element) {
        _makeFunctionsPublic(state);
        state.initialize(element);
    };

    // ***************************************************************
    // Private functions start here. Private functions start with underscore.
    // ***************************************************************

    /**
     * @function _makeFunctionsPublic
     *
     * Functions which will be accessible via 'state' object. When called,
     * these functions will get the 'state'
     * object as a context.
     *
     * @param {object} state The object containg the state (properties,
     *     methods, modules) of the Video player.
     */
    function _makeFunctionsPublic(state) {
        state.setSpeed      = _.bind(setSpeed, state);
        state.youtubeId     = _.bind(youtubeId, state);
        state.getDuration   = _.bind(getDuration, state);
        state.trigger       = _.bind(trigger, state);
        state.stopBuffering = _.bind(stopBuffering, state);

        // Old private functions. Now also public so that can be
        // tested by Jasmine.

        state.initialize          = _.bind(initialize, state);
        state.parseSpeed          = _.bind(parseSpeed, state);
        state.fetchMetadata       = _.bind(fetchMetadata, state);
        state.parseYoutubeStreams = _.bind(parseYoutubeStreams, state);
        state.parseVideoSources   = _.bind(parseVideoSources, state);
        state.getVideoMetadata    = _.bind(getVideoMetadata, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their
    //     initial configuration. Also make the created DOM elements available
    //     via the 'state' object. Much easier to work this way - you don't
    //     have to do repeated jQuery element selects.
    function _renderElements(state) {
        // Launch embedding of actual video content, or set it up so that it
        // will be done as soon as the appropriate video player (YouTube or
        // stand-alone HTML5) is loaded, and can handle embedding.
        //
        // Note that the loading of stand alone HTML5 player API is handled by
        // Require JS. At the time when we reach this code, the stand alone
        // HTML5 player is already loaded, so no further testing in that case
        // is required.
        var onPlayerReadyFunc;
        if (
            (
                (state.videoType === 'youtube') &&
                (window.YT) &&
                (window.YT.Player)
            ) ||
            (state.videoType === 'html5')
        ) {
            VideoPlayer(state);
        } else {
            if (state.videoType === 'youtube') {
                onPlayerReadyFunc = 'onYouTubePlayerAPIReady';
            } else {
                onPlayerReadyFunc = 'onHTML5PlayerAPIReady';
            }
            window[onPlayerReadyFunc] = _.bind(VideoPlayer, window, state);
        }
    }

    // function _configureCaptions(state)
    //     Configure displaying of captions.
    //
    //     Option
    //         this.config.show_captions = true | false
    //
    //     Defines whether or not captions are shown on first viewing.
    //
    //     Option
    //          this.hide_captions = true | false
    //
    //     represents the user's choice of having the subtitles shown or
    //     hidden. This choice is stored in cookies.
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
    //     By default we will be forcing HTML5 player mode. Only in the case
    //     when, after initializtion, we will get one available playback rate,
    //     we will change to Flash player mode. There is a need to store this
    //     setting in cookies because otherwise we will have to change from
    //     HTML5 to Flash on every page load in a browser that doesn't fully
    //     support HTML5. When we have this setting in cookies, we can select
    //     the proper mode from the start (not having to change mode later on).
    function _setPlayerMode(state) {
        (function (currentPlayerMode) {
            if (
                (currentPlayerMode === 'html5') ||
                (currentPlayerMode === 'flash')
            ) {
                state.currentPlayerMode = currentPlayerMode;
            } else {
                $.cookie('current_player_mode', 'html5', {
                    expires: 3650,
                    path: '/'
                });
                state.currentPlayerMode = 'html5';
            }

            console.log(
                '[Video info]: YouTube player mode is "' +
                state.currentPlayerMode + '".'
            );
        }($.cookie('current_player_mode')));
    }

    // function _parseYouTubeIDs(state)
    //     The function parse YouTube stream ID's.
    //     @return
    //         false: We don't have YouTube video IDs to work with; most likely
    //             we have HTML5 video sources.
    //         true: Parsing of YouTube video IDs went OK, and we can proceed
    //             onwards to play YouTube videos.
    function _parseYouTubeIDs(state) {
        if (state.parseYoutubeStreams(state.config.youtubeStreams)) {
            state.videoType = 'youtube';

            return true;
        }

        console.log(
            '[Video info]: Youtube Video IDs are incorrect or absent.'
        );

        return false;
    }

    // function _prepareHTML5Video(state)
    // The function prepare HTML5 video, parse HTML5
    // video sources etc.
    function _prepareHTML5Video(state, html5Mode) {
        state.parseVideoSources(
            {
                mp4: state.config.mp4Source,
                webm: state.config.webmSource,
                ogg: state.config.oggSource
            }
        );

        if (html5Mode) {
            state.speeds = ['0.75', '1.0', '1.25', '1.50'];
            state.videos = {
                '0.75': state.config.sub,
                '1.0':  state.config.sub,
                '1.25': state.config.sub,
                '1.5':  state.config.sub
            };
        }

        // We must have at least one non-YouTube video source available.
        // Otherwise, return a negative.
        if (
            state.html5Sources.webm === null &&
            state.html5Sources.mp4 === null &&
            state.html5Sources.ogg === null
        ) {
            state.el.find('.video-player div').addClass('hidden');
            state.el.find('.video-player h3').removeClass('hidden');

            console.log(
                '[Video info]: Non-youtube video sources aren\'t available.'
            );

            return false;
        }

        state.videoType = 'html5';

        if (!state.config.sub || !state.config.sub.length) {
            state.config.sub = '';
            state.config.show_captions = false;
        }

        state.setSpeed($.cookie('video_speed'));

        return true;
    }

    function _setConfigurations(state) {
        _configureCaptions(state);
        _setPlayerMode(state);

        // Possible value are: 'visible', 'hiding', and 'invisible'.
        state.controlState = 'visible';
        state.controlHideTimeout = null;
        state.captionState = 'visible';
        state.captionHideTimeout = null;
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this'
    // keyword) is the 'state' object. The magic private function that makes
    // them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    // function initialize(element)
    // The function set initial configuration and preparation.

    function initialize(element) {
        var _this = this, tempYtTestTimeout;
        // This is used in places where we instead would have to check if an
        // element has a CSS class 'fullscreen'.
        this.isFullScreen = false;

        // The parent element of the video, and the ID.
        this.el = $(element).find('.video');
        this.elVideoWrapper = this.el.find('.video-wrapper');
        this.id = this.el.attr('id').replace(/video_/, '');

        console.log(
            '[Video info]: Initializing video with id "' + this.id + '".'
        );

        // We store all settings passed to us by the server in one place. These
        // are "read only", so don't modify them. All variable content lives in
        // 'state' object.
        this.config = {
            element: element,

            start:              this.el.data('start'),
            end:                this.el.data('end'),

            caption_data_dir:   this.el.data('caption-data-dir'),
            caption_asset_path: this.el.data('caption-asset-path'),
            show_captions:      (
                                    this.el.data('show-captions')
                                        .toString().toLowerCase() === 'true'
                                ),
            youtubeStreams:     this.el.data('streams'),

            autohideHtml5:      (
                                    this.el.data('autohide-html5')
                                        .toString().toLowerCase() === 'true'
                                ),

            sub:                this.el.data('sub'),
            mp4Source:          this.el.data('mp4-source'),
            webmSource:         this.el.data('webm-source'),
            oggSource:          this.el.data('ogg-source'),

            ytTestUrl:   this.el.data('yt-test-url'),

            fadeOutTimeout:     1400,

            availableQualities: ['hd720', 'hd1080', 'highres']
        };

        console.log('this.config.autohideHtml5 = ' + this.config.autohideHtml5);

        // Check if the YT test timeout has been set. If not, or it is in
        // improper format, then set to default value.
        tempYtTestTimeout = parseInt(this.el.data('yt-test-timeout'), 10);
        if (!isFinite(tempYtTestTimeout)) {
            tempYtTestTimeout = 1500;
        }
        this.config.ytTestTimeout = tempYtTestTimeout;

        if (!(_parseYouTubeIDs(this))) {

            // If we do not have YouTube ID's, try parsing HTML5 video sources.
            if (!_prepareHTML5Video(this, true)) {

                // Non-YouTube sources were not found either.
                return;
            }

            console.log('[Video info]: Start player in HTML5 mode.');

            _setConfigurations(this);
            _renderElements(this);
        } else {
            if (!this.youtubeXhr) {
                this.youtubeXhr = this.getVideoMetadata();
            }

            this.youtubeXhr
                .always(function (json, status) {
                    var err = $.isPlainObject(json.error) ||
                                (
                                    status !== 'success' &&
                                    status !== 'notmodified'
                                );
                    if (err) {
                        console.log(
                            '[Video info]: YouTube returned an error for ' +
                            'video with id "' + _this.id + '".'
                        );

                        // When the youtube link doesn't work for any reason
                        // (for example, the great firewall in china) any
                        // alternate sources should automatically play.
                        if (!_prepareHTML5Video(_this)) {
                            console.log(
                                '[Video info]: Continue loading ' +
                                'YouTube video.'
                            );

                            // Non-YouTube sources were not found either.

                            _this.el.find('.video-player div')
                                .removeClass('hidden');
                            _this.el.find('.video-player h3')
                                .addClass('hidden');

                            // If in reality the timeout was to short, try to
                            // continue loading the YouTube video anyways.
                            _this.fetchMetadata();
                            _this.parseSpeed();
                        } else {
                            console.log(
                                '[Video info]: Change player mode to HTML5.'
                            );

                            // In-browser HTML5 player does not support quality
                            // control.
                            _this.el.find('a.quality_control').hide();
                        }
                    } else {
                        console.log(
                            '[Video info]: Start player in YouTube mode.'
                        );

                        _this.fetchMetadata();
                        _this.parseSpeed();
                    }

                    _setConfigurations(_this);
                    _renderElements(_this);
                });
        }
    }

    // function parseYoutubeStreams(state, youtubeStreams)
    //
    //     Take a string in the form:
    //         "iCawTYPtehk:0.75,KgpclqP-LBA:1.0,9-2670d5nvU:1.5"
    //     parse it, and make it available via the 'state' object. If we are
    //     not given a string, or it's length is zero, then we return false.
    //
    //     @return
    //         false: We don't have YouTube video IDs to work with; most likely
    //             we have HTML5 video sources.
    //         true: Parsing of YouTube video IDs went OK, and we can proceed
    //             onwards to play YouTube videos.
    function parseYoutubeStreams(youtubeStreams) {
        var _this;

        if (
            typeof youtubeStreams === 'undefined' ||
            youtubeStreams.length === 0
        ) {
            return false;
        }

        _this = this;
        this.videos = {};

        $.each(youtubeStreams.split(/,/), function (index, video) {
            var speed;

            video = video.split(/:/);
            speed = parseFloat(video[0]).toFixed(2).replace(/\.00$/, '.0');

            _this.videos[speed] = video[1];
        });

        return true;
    }

    // function parseVideoSources(, mp4Source, webmSource, oggSource)
    //
    //     Take the HTML5 sources (URLs of videos), and make them available
    //     explictly for each type of video format (mp4, webm, ogg).
    function parseVideoSources(sources) {
        var _this = this,
            v = document.createElement('video'),
            sourceCodecs = {
                mp4: 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"',
                webm: 'video/webm; codecs="vp8, vorbis"',
                ogg: 'video/ogg; codecs="theora"'
            };

        this.html5Sources = {
            mp4: null,
            webm: null,
            ogg: null
        };

        $.each(sources, function (name, source) {
            if (source && source.length) {
                if (
                    Boolean(
                        v.canPlayType &&
                        v.canPlayType(sourceCodecs[name]).replace(/no/, '')
                    )
                ) {
                    _this.html5Sources[name] = source;
                }
            }
        });
    }

    // function fetchMetadata()
    //
    //     When dealing with YouTube videos, we must fetch meta data that has
    //     certain key facts not available while the video is loading. For
    //     example the length of the video can be determined from the meta
    //     data.
    function fetchMetadata() {
        var _this = this;

        this.metadata = {};

        $.each(this.videos, function (speed, url) {
            _this.getVideoMetadata(url, function (data) {
                if (data.data) {
                    _this.metadata[data.data.id] = data.data;
                }
            });
        });
    }

    // function parseSpeed()
    //
    //     Create a separate array of available speeds.
    function parseSpeed() {
        this.speeds = ($.map(this.videos, function (url, speed) {
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

    function getVideoMetadata(url, callback) {
        var successHandler, xhr;

        if (typeof url !== 'string') {
            url = this.videos['1.0'] || '';
        }
        successHandler = ($.isFunction(callback)) ? callback : null;
        xhr = $.ajax({
            url: this.config.ytTestUrl + url + '?v=2&alt=jsonc',
            dataType: 'jsonp',
            timeout: this.config.ytTestTimeout,
            success: successHandler
        });

        return xhr;
    }

    function stopBuffering() {
        var video;

        if (this.videoType === 'html5') {
            // HTML5 player haven't default way to abort bufferization.
            // In this case we simply resetting source and call load().
            video = this.videoPlayer.player.video;
            video.src = '';
            video.load();
        }
    }

    function youtubeId(speed) {
        return this.videos[speed || this.speed];
    }

    function getDuration() {
        return this.metadata[this.youtubeId()].duration;
    }

    /*
     * The trigger() function will assume that the @objChain is a complete
     * chain with a method (function) at the end. It will call this function.
     * So for example, when trigger() is called like so:
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

        // At the end of the loop the variable 'tmpObj' will either be the
        // correct object/function to trigger/invoke. If the 'chain' chain of
        // object is incorrect (one of the link is non-existent), then the loop
        // will immediately exit.
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
