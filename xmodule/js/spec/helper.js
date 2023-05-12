/* global _ */

(function() {
    'use strict';

    // eslint-disable-next-line no-var
    var origAjax = $.ajax;

    // eslint-disable-next-line no-var
    var stubbedYT = {
        Player: function() {
            /* eslint-disable-next-line no-undef, no-var */
            var Player = jasmine.createSpyObj(
                'YT.Player',
                [
                    'cueVideoById', 'getVideoEmbedCode', 'getCurrentTime',
                    'getPlayerState', 'getVolume', 'setVolume',
                    'loadVideoById', 'getAvailablePlaybackRates', 'playVideo',
                    'pauseVideo', 'seekTo', 'getDuration', 'setPlaybackRate',
                    'getAvailableQualityLevels', 'getPlaybackQuality',
                    'setPlaybackQuality', 'destroy'
                ]
            );

            Player.getDuration.and.returnValue(60);
            Player.getAvailablePlaybackRates.and.returnValue([0.50, 1.0, 1.50, 2.0]);
            Player.getAvailableQualityLevels.and.returnValue(
                ['highres', 'hd1080', 'hd720', 'large', 'medium', 'small']
            );

            return Player;
        },

        PlayerState: {
            UNSTARTED: -1,
            ENDED: 0,
            PLAYING: 1,
            PAUSED: 2,
            BUFFERING: 3,
            CUED: 5
        },
        ready: function(f) {
            return f();
        }
    };
    // eslint-disable-next-line no-undef
    jasmine.YT = stubbedYT;
    // Stub YouTube API.
    window.YT = stubbedYT;

    window.STATUS = window.YT.PlayerState;

    window.onTouchBasedDevice = function() {
        return navigator.userAgent.match(/iPhone|iPod|iPad/i);
    };

    // eslint-disable-next-line no-undef
    jasmine.stubbedCaption = {
        end: [
            3120, 6270, 8490, 21620, 24920, 25750, 27900, 34380, 35550, 40250
        ],
        start: [
            1180, 3120, 6270, 14910, 21620, 24920, 25750, 27900, 34380, 35550
        ],
        text: [
            'MICHAEL CIMA: So let\'s do the first one here.',
            'Vacancies, where do they come from?',
            'Well, imagine a perfect crystal.',
            'Now we know at any temperature other than absolute zero '
                + 'there\'s enough',
            'energy going around that some atoms will have more energy',
            'than others, right?',
            'There\'s a distribution.',
            'If I plot energy here and number, these atoms in the crystal '
                + 'will have a',
            'distribution of energy.',
            'And some will have quite a bit of energy, just for a moment.'
        ]
    };

    // Time waitsFor() should wait for before failing a test.
    window.WAIT_TIMEOUT = 5000;

    // eslint-disable-next-line no-undef
    jasmine.getFixtures().fixturesPath += 'fixtures';

    // eslint-disable-next-line no-undef
    jasmine.stubbedMetadata = {
        '7tqY6eQzVhE': {
            contentDetails: {
                id: '7tqY6eQzVhE',
                duration: 'PT5M0S'
            }
        },
        cogebirgzzM: {
            contentDetails: {
                id: 'cogebirgzzM',
                duration: 'PT3M20S'
            }
        },
        abcdefghijkl: {
            contentDetails: {
                id: 'abcdefghijkl',
                duration: 'PT6M40S'
            }
        },
        bogus: {
            contentDetails: {
                duration: 'PT1M40S'
            }
        }
    };

    // eslint-disable-next-line no-undef
    jasmine.fireEvent = function(el, eventName) {
        // eslint-disable-next-line no-var
        var event;

        if (document.createEvent) {
            event = document.createEvent('HTMLEvents');
            event.initEvent(eventName, true, true);
        } else {
            event = document.createEventObject();
            event.eventType = eventName;
        }

        event.eventName = eventName;

        if (document.createEvent) {
            el.dispatchEvent(event);
        } else {
            el.fireEvent('on' + event.eventType, event);
        }
    };

    // eslint-disable-next-line no-undef
    jasmine.stubbedHtml5Speeds = ['0.75', '1.0', '1.25', '1.50', '2.0'];

    // eslint-disable-next-line no-undef
    jasmine.stubRequests = function() {
        // eslint-disable-next-line no-var
        var spy = $.ajax;
        // eslint-disable-next-line no-undef
        if (!jasmine.isSpy($.ajax)) {
            // eslint-disable-next-line no-undef
            spy = spyOn($, 'ajax');
        }

        return spy.and.callFake(function(settings) {
            // eslint-disable-next-line no-var
            var match = settings.url
                    .match(/googleapis\.com\/.+\/videos\/\?id=(.+)&part=contentDetails/),
                status, callCallback;
            if (match) {
                status = match[1].split('_');
                if (status && status[0] === 'status') {
                    callCallback = function(callback) {
                        callback.call(window, {}, status[1]);
                    };

                    return {
                        always: callCallback,
                        error: callCallback,
                        done: callCallback
                    };
                } else if (settings.success) {
                    return settings.success({
                        // eslint-disable-next-line no-undef
                        items: jasmine.stubbedMetadata[match[1]]
                    });
                } else {
                    return {
                        always: function(callback) {
                            return callback.call(window, {}, 'success');
                        },
                        done: function(callback) {
                            return callback.call(window, {}, 'success');
                        }
                    };
                }
            } else if (settings.url.match(/transcript\/translation\/.+$/)) {
                // eslint-disable-next-line no-undef
                return settings.success(jasmine.stubbedCaption);
            } else if (settings.url === '/transcript/available_translations') {
                return settings.success(['uk', 'de']);
            } else if (settings.url.match(/.+\/problem_get$/)) {
                return settings.success({
                    html: window.readFixtures('problem_content.html')
                });
            } else if (
                settings.url === '/calculate'
                || settings.url.match(/.+\/goto_position$/)
                || settings.url.match(/event$/)
                || settings.url.match(/.+\/problem_(check|reset|show|save)$/)
            ) {
                // Do nothing.
                return {};
            } else if (settings.url === '/save_user_state') {
                return {success: true};
            // eslint-disable-next-line no-undef
            } else if (settings.url.match(new RegExp(jasmine.getFixtures().fixturesPath + '.+', 'g'))) {
                return origAjax(settings);
            } else {
                return $.ajax.and.callThrough();
            }
        });
    };

    // Stub jQuery.cookie module.
    // eslint-disable-next-line no-undef
    $.cookie = jasmine.createSpy('jQuery.cookie').and.returnValue('1.0');

    // # Stub jQuery.qtip module.
    // eslint-disable-next-line no-undef
    $.fn.qtip = jasmine.createSpy('jQuery.qtip');

    // Stub jQuery.scrollTo module.
    // eslint-disable-next-line no-undef
    $.fn.scrollTo = jasmine.createSpy('jQuery.scrollTo');

    // eslint-disable-next-line no-undef
    jasmine.initializePlayer = function(fixture, params) {
        // eslint-disable-next-line no-var
        var state, metadata;

        if (_.isString(fixture)) {
            // `fixture` is a name of a fixture file.
            loadFixtures(fixture);
        } else {
            // `fixture` is not a string. The first parameter is an object?
            if (_.isObject(fixture)) {
                // The first parameter contains attributes for the main video
                // DIV element.
                params = fixture;
            }

            // "video_all.html" is the default HTML template for HTML5 video.
            loadFixtures('video_all.html');
        }

        // If `params` is an object, assign its properties as data attributes
        // to the main video DIV element.
        if (_.isObject(params)) {
            metadata = _.extend($('#video_id').data('metadata'), params);
            $('#video_id').data('metadata', metadata);
        }

        // eslint-disable-next-line no-undef
        jasmine.stubRequests();
        state = new window.Video('#example');

        state.resizer = (function() {
            // eslint-disable-next-line no-var
            var methods = [
                    'align',
                    'alignByWidthOnly',
                    'alignByHeightOnly',
                    'setParams',
                    'setMode',
                    'setElement'
                ],
                obj = {},
                delta = {
                    // eslint-disable-next-line no-undef
                    add: jasmine.createSpy().and.returnValue(obj),
                    // eslint-disable-next-line no-undef
                    substract: jasmine.createSpy().and.returnValue(obj),
                    // eslint-disable-next-line no-undef
                    reset: jasmine.createSpy().and.returnValue(obj)
                };

            $.each(methods, function(index, method) {
                // eslint-disable-next-line no-undef
                obj[method] = jasmine.createSpy(method).and.returnValue(obj);
            });

            obj.delta = delta;

            return obj;
        }());

        // We return the `state` object of the newly initialized Video.
        return state;
    };

    // eslint-disable-next-line no-undef
    jasmine.initializeHLSPlayer = function(params) {
        // eslint-disable-next-line no-undef
        return jasmine.initializePlayer('video_hls.html', params);
    };

    // eslint-disable-next-line no-undef
    jasmine.initializePlayerYouTube = function(params) {
        // "video.html" contains HTML template for a YouTube video.
        // eslint-disable-next-line no-undef
        return jasmine.initializePlayer('video.html', params);
    };

    // eslint-disable-next-line no-undef
    jasmine.DescribeInfo = function(description, specDefinitions) {
        this.description = description;
        this.specDefinitions = specDefinitions;
    };

    // This HTML Fullscreen API mock should use promises or async functions
    // as the spec defines. We do not use them here because we're locked
    // in to a version of jasmine that doesn't fully support async functions
    // or promises. This mock also assumes that if non-vendor prefixed methods
    // and properties are missing, then we'll use mozilla prefixed names since
    // automated tests happen in firefox.
    // eslint-disable-next-line no-undef
    jasmine.mockFullscreenAPI = function() {
        // eslint-disable-next-line no-var
        var fullscreenElement;
        // eslint-disable-next-line no-var
        var vendorChangeEvent = 'fullscreenEnabled' in document
            ? 'fullscreenchange' : 'mozfullscreenchange';
        // eslint-disable-next-line no-var
        var vendorRequestFullscreen = 'requestFullscreen' in window.HTMLElement.prototype
            ? 'requestFullscreen' : 'mozRequestFullScreen';
        // eslint-disable-next-line no-var
        var vendorExitFullscreen = 'exitFullscreen' in document
            ? 'exitFullscreen' : 'mozCancelFullScreen';
        // eslint-disable-next-line no-var
        var vendorFullscreenElement = 'fullscreenEnabled' in document
            ? 'fullscreenElement' : 'mozFullScreenElement';

        // eslint-disable-next-line no-undef
        spyOn(window.HTMLElement.prototype, vendorRequestFullscreen).and.callFake(function() {
            fullscreenElement = this;
            document.dispatchEvent(new Event(vendorChangeEvent));
        });

        // eslint-disable-next-line no-undef
        spyOn(document, vendorExitFullscreen).and.callFake(function() {
            fullscreenElement = null;
            document.dispatchEvent(new Event(vendorChangeEvent));
        });

        // eslint-disable-next-line no-undef
        spyOnProperty(document, vendorFullscreenElement).and.callFake(function() {
            return fullscreenElement;
        });
    };
}).call(this);
