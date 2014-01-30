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
['video/03_video_player.js', 'video/00_cookie_storage.js'],
function (VideoPlayer, CookieStorage) {
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

        state.initialize(element)
            .done(function () {
                // On iPhones and iPods native controls are used.
                if (/iP(hone|od)/i.test(state.isTouch[0])) {
                    _hideWaitPlaceholder(state);
                    state.el.trigger('initialize', arguments);

                    return false;
                }

                _initializeModules(state)
                    .done(function () {
                        // On iPad ready state occurs just after start playing.
                        // We hide controls before video starts playing.
                        if (/iPad|Android/i.test(state.isTouch[0])) {
                            state.el.on('play', _.once(function() {
                                state.trigger('videoControl.show', null);
                            }));
                        } else {
                        // On PC show controls immediately.
                            state.trigger('videoControl.show', null);
                        }

                        _hideWaitPlaceholder(state);
                        state.el.trigger('initialize', arguments);
                    });
            });
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
        var methodsDict = {
            bindTo: bindTo,
            fetchMetadata: fetchMetadata,
            getCurrentLanguage: getCurrentLanguage,
            getDuration: getDuration,
            getVideoMetadata: getVideoMetadata,
            initialize: initialize,
            parseSpeed: parseSpeed,
            parseVideoSources: parseVideoSources,
            parseYoutubeStreams: parseYoutubeStreams,
            setSpeed: setSpeed,
            stopBuffering: stopBuffering,
            trigger: trigger,
            youtubeId: youtubeId
        };

        bindTo(methodsDict, state, state);
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
        var video;

        if(state.videoType === 'youtube') {
            YT.ready(function() {
                video = VideoPlayer(state);

                state.modules.push(video);
                state.__dfd__.resolve();
            });
        } else {
            video = VideoPlayer(state);

            state.modules.push(video);
            state.__dfd__.resolve();
        }
    }

    // function _configureCaptions(state)
    //     Configure displaying of captions.
    //
    //     Option
    //         this.config.showCaptions = true | false
    //
    //     Defines whether or not captions are shown on first viewing.
    //
    //     Option
    //          this.hide_captions = true | false
    //
    //     represents the user's choice of having the subtitles shown or
    //     hidden. This choice is stored in cookies.
    function _configureCaptions(state) {
        if (state.config.showCaptions) {
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
        state.currentPlayerMode = 'html5';
    }

    // function _parseYouTubeIDs(state)
    //     The function parse YouTube stream ID's.
    //     @return
    //         false: We don't have YouTube video IDs to work with; most likely
    //             we have HTML5 video sources.
    //         true: Parsing of YouTube video IDs went OK, and we can proceed
    //             onwards to play YouTube videos.
    function _parseYouTubeIDs(state) {
        if (state.parseYoutubeStreams(state.config.streams)) {
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
    function _prepareHTML5Video(state) {
        state.parseVideoSources(
            {
                mp4: state.config.mp4Source,
                webm: state.config.webmSource,
                ogg: state.config.oggSource
            }
        );

        state.speeds = ['0.75', '1.0', '1.25', '1.50'];
        state.videos = {
            '0.75': state.config.sub,
            '1.0':  state.config.sub,
            '1.25': state.config.sub,
            '1.50':  state.config.sub
        };

        // We must have at least one non-YouTube video source available.
        // Otherwise, return a negative.
        if (
            state.html5Sources.webm === null &&
            state.html5Sources.mp4 === null &&
            state.html5Sources.ogg === null
        ) {

            // TODO: use 1 class to work with.
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
            state.config.showCaptions = false;
        }
        state.setSpeed(state.speed);

        return true;
    }

    function _hideWaitPlaceholder(state) {
        state.el
            .addClass('is-initialized')
            .find('.spinner')
            .attr({
                'aria-hidden': 'true',
                'tabindex': -1
            });
    }

    function _setConfigurations(state) {
        _configureCaptions(state);
        _setPlayerMode(state);

        // Possible value are: 'visible', 'hiding', and 'invisible'.
        state.controlState = 'visible';
        state.controlHideTimeout = null;
        state.captionState = 'invisible';
        state.captionHideTimeout = null;
    }

    function _initializeModules(state) {
        var dfd = $.Deferred(),
            modulesList = $.map(state.modules, function(module) {
                if ($.isFunction(module)) {
                    return module(state);
                } else if ($.isPlainObject(module)) {
                    return module;
                }
        });

        $.when.apply(null, modulesList)
            .done(dfd.resolve);

        return dfd.promise();
    }

    function _getConfiguration(data) {
            var isBoolean = function (value) {
                    var regExp = /^true$/i;
                    return regExp.test(value.toString());
                },
                // List of keys that will be extracted form the configuration.
                extractKeys = ['speed', 'transcript-language'],
                // Compatibility keys used to change names of some parameters in
                // the final configuration.
                compatKeys = {
                    'start': 'startTime',
                    'end': 'endTime'
                },
                // Conversions used to pre-process some configuration data.
                conversions = {
                    'showCaptions': isBoolean,
                    'autoplay': isBoolean,
                    'autohideHtml5': isBoolean,
                    'ytTestTimeout': function (value) {
                        value = parseInt(value, 10);

                        if (!isFinite(value)) {
                            value = 1500;
                        }

                        return value;
                    },
                    'startTime': function (value) {
                        value = parseInt(value, 10);

                        if (!isFinite(value) || value < 0) {
                            return 0;
                        }

                        return value;
                    },
                    'endTime': function (value) {
                        value = parseInt(value, 10);

                        if (!isFinite(value) || value === 0) {
                            return null;
                        }

                        return value;
                     }
                },
                config = {};

            $.each(data, function(option, value) {
                // Extract option that is in `extractKeys`.
                if ($.inArray(option, extractKeys) !== -1) {
                    return;
                }

                // Change option name to key that is in `compatKeys`.
                if (compatKeys[option]) {
                    option = compatKeys[option];
                }

                // Pre-process data.
                if (conversions[option]) {
                    if ($.isFunction(conversions[option])) {
                        value = conversions[option].call(this, value);
                    } else {
                        throw new TypeError(option + ' is not a function.');
                    }
                }
                config[option] = value;
            });

            return config;
        }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this'
    // keyword) is the 'state' object. The magic private function that makes
    // them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************


    // function bindTo(methodsDict, obj, context, rewrite)
    // Creates a new function with specific context and assigns it to the provided
    // object.
    function bindTo(methodsDict, obj, context, rewrite) {
        $.each(methodsDict, function(name, method) {
            if (_.isFunction(method)) {

                if (_.isUndefined(rewrite)) {
                    rewrite = true;
                }

                if (_.isUndefined(obj[name]) || rewrite) {
                    obj[name] = _.bind(method, context);
                }
            }
        });
    }

    // function initialize(element)
    // The function set initial configuration and preparation.

    function initialize(element) {
        var self = this,
            el = $(element).find('.video'),
            container = el.find('.video-wrapper'),
            id = el.attr('id').replace(/video_/, ''),
            __dfd__ = $.Deferred(),
            isTouch = onTouchBasedDevice() || '',
            storage = CookieStorage('video_player'),

            speed = storage.getItem('video_speed_' + id) ||
                el.data('speed') ||
                storage.getItem('general_speed') ||
                el.data('general-speed') ||
                '1.0',

            lang = storage.getItem('language') || el.data('transcript-language') || 'en';

        if (isTouch) {
            el.addClass('is-touch');
        }

        $.extend(this, {
            __dfd__: __dfd__,
            el: el,
            container: container,
            currentVolume: 100,
            id: id,
            isFullScreen: false,
            isTouch: isTouch,
            speed: Number(speed).toFixed(2).replace(/\.00$/, '.0'),
            lang: lang,
            storage: storage
        });

        console.log(
            '[Video info]: Initializing video with id "' + id + '".'
        );

        // We store all settings passed to us by the server in one place. These
        // are "read only", so don't modify them. All variable content lives in
        // 'state' object.
        // jQuery .data() return object with keys in lower camelCase format.
        this.config = $.extend({}, _getConfiguration(el.data()), {
            element: element,
            fadeOutTimeout:     1400,
            captionsFreezeTime: 10000,
            availableQualities: ['hd720', 'hd1080', 'highres']
        });

        if (this.config.endTime < this.config.startTime) {
            this.config.endTime = null;
        }

        if (!(_parseYouTubeIDs(this))) {

            // If we do not have YouTube ID's, try parsing HTML5 video sources.
            if (!_prepareHTML5Video(this)) {

                __dfd__.reject();
                // Non-YouTube sources were not found either.
                return __dfd__.promise();
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
                            'video with id "' + id + '".'
                        );

                        // When the youtube link doesn't work for any reason
                        // (for example, the great firewall in china) any
                        // alternate sources should automatically play.
                        if (!_prepareHTML5Video(self)) {
                            console.log(
                                '[Video info]: Continue loading ' +
                                'YouTube video.'
                            );

                            // Non-YouTube sources were not found either.

                            el.find('.video-player div')
                                .removeClass('hidden');
                            el.find('.video-player h3')
                                .addClass('hidden');

                            // If in reality the timeout was to short, try to
                            // continue loading the YouTube video anyways.
                            self.fetchMetadata();
                            self.parseSpeed();
                        } else {
                            console.log(
                                '[Video info]: Change player mode to HTML5.'
                            );

                            // In-browser HTML5 player does not support quality
                            // control.
                            el.find('a.quality_control').hide();
                        }
                    } else {
                        console.log(
                            '[Video info]: Start player in YouTube mode.'
                        );

                        self.fetchMetadata();
                        self.parseSpeed();
                    }

                    _setConfigurations(self);
                    _renderElements(self);
                });
        }

        return __dfd__.promise();
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
        var _this = this,
            metadataXHRs = [];

        this.metadata = {};

        $.each(this.videos, function (speed, url) {
            var xhr = _this.getVideoMetadata(url, function (data) {
                if (data.data) {
                    _this.metadata[data.data.id] = data.data;
                }
            });

            metadataXHRs.push(xhr);
        });

        $.when.apply(this, metadataXHRs).done(function () {
            _this.el.trigger('metadata_received');

            // Not only do we trigger the "metadata_received" event, we also
            // set a flag to notify that metadata has been received. This
            // allows for code that will miss the "metadata_received" event
            // to know that metadata has been received. This is important in
            // cases when some code will subscribe to the "metadata_received"
            // event after it has been triggered.
            _this.youtubeMetadataReceived = true;

        });
    }

    // function parseSpeed()
    //
    //     Create a separate array of available speeds.
    function parseSpeed() {
        this.speeds = ($.map(this.videos, function (url, speed) {
            return speed;
        })).sort();
    }

    function setSpeed(newSpeed, updateStorage) {
        // Possible speeds for each player type.
        // flash =          [0.75, 1, 1.25, 1.5]
        // html5 =          [0.75, 1, 1.25, 1.5]
        // youtube html5 =  [0.25, 0.5, 1, 1.5, 2]
        var map = {
                '0.25': '0.75',
                '0.50': '0.75',
                '0.75': '0.50',
                '1.25': '1.50',
                '2.0': '1.50'
            },
            useSession = true;

        if (_.contains(this.speeds, newSpeed)) {
            this.speed = newSpeed;
        } else {
            newSpeed = map[newSpeed];
            this.speed = _.contains(this.speeds, newSpeed) ? newSpeed : '1.0';
        }

        if (updateStorage) {
            this.storage.setItem('video_speed_' + this.id, this.speed, useSession);
            this.storage.setItem('general_speed', this.speed, useSession);
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
        return this.videos[speed || this.speed] || this.videos['1.0'];
    }

    function getDuration() {
        try {
            return this.metadata[this.youtubeId()].duration;
        } catch (err) {
            return this.metadata[this.youtubeId('1.0')].duration;
        }
    }

    function getCurrentLanguage() {
        return this.lang || 'en';
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
    function trigger(objChain) {
        var extraParameters = Array.prototype.slice.call(arguments, 1),
            i, tmpObj, chain;

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

        tmpObj.apply(this, extraParameters);

        return true;
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
