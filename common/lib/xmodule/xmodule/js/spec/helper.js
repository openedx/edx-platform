(function ($, undefined) {
    // Stub YouTube API.
    window.YT = {
        Player: function () {
            var Player = jasmine.createSpyObj(
                'YT.Player',
                [
                    'cueVideoById', 'getVideoEmbedCode', 'getCurrentTime',
                    'getPlayerState', 'getVolume', 'setVolume',
                    'loadVideoById', 'getAvailablePlaybackRates', 'playVideo',
                    'pauseVideo', 'seekTo', 'getDuration', 'setPlaybackRate',
                    'getPlaybackQuality'
                ]
            );

            Player.getDuration.andReturn(60);
            Player.getAvailablePlaybackRates.andReturn([0.50, 1.0, 1.50, 2.0]);

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
        ready: function (f) {
            return f();
        }
    };

    window.STATUS = window.YT.PlayerState;

    window.onTouchBasedDevice = function () {
        return navigator.userAgent.match(/iPhone|iPod|iPad/i);
    };

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
            'Now we know at any temperature other than absolute zero ' +
                'there\'s enough',
            'energy going around that some atoms will have more energy',
            'than others, right?',
            'There\'s a distribution.',
            'If I plot energy here and number, these atoms in the crystal ' +
                'will have a',
            'distribution of energy.',
            'And some will have quite a bit of energy, just for a moment.'
        ]
    };

    // Time waitsFor() should wait for before failing a test.
    window.WAIT_TIMEOUT = 5000;

    jasmine.getFixtures().fixturesPath += 'fixtures';

    jasmine.stubbedMetadata = {
        '7tqY6eQzVhE': {
            id: '7tqY6eQzVhE',
            duration: 300
        },
        'cogebirgzzM': {
            id: 'cogebirgzzM',
            duration: 200
        },
        'abcdefghijkl': {
            id: 'abcdefghijkl',
            duration: 400
        },
        bogus: {
            duration: 100
        }
    };

    jasmine.fireEvent = function (el, eventName) {
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

    jasmine.stubbedHtml5Speeds = ['0.75', '1.0', '1.25', '1.50'];

    jasmine.stubRequests = function () {
        var spy = $.ajax;

        if (!($.ajax.isSpy)) {
            spy = spyOn($, 'ajax');
        }
        return spy.andCallFake(function (settings) {
            var match, status, callCallback;
            if (
                match = settings.url
                    .match(/youtube\.com\/.+\/videos\/(.+)\?v=2&alt=jsonc/)
            ) {
                status = match[1].split('_');
                if (status && status[0] === 'status') {
                    callCallback = function (callback) {
                        callback.call(window, {}, status[1]);
                    };

                    return {
                        always: callCallback,
                        error: callCallback,
                        done: callCallback
                    };
                } else if (settings.success) {
                    return settings.success({
                        data: jasmine.stubbedMetadata[match[1]]
                    });
                } else {
                    return {
                        always: function (callback) {
                            return callback.call(window, {}, 'success');
                        },
                        done: function (callback) {
                            return callback.call(window, {}, 'success');
                        }
                    };
                }
            } else if (settings.url == '/transcript/translation') {
                return settings.success(jasmine.stubbedCaption);
            } else if (settings.url.match(/.+\/problem_get$/)) {
                return settings.success({
                    html: readFixtures('problem_content.html')
                });
            } else if (
                settings.url === '/calculate' ||
                settings.url.match(/.+\/goto_position$/) ||
                settings.url.match(/event$/) ||
                settings.url.match(/.+\/problem_(check|reset|show|save)$/)
            ) {
                // Do nothing.
            } else if (settings.url == '/save_user_state') {
                return {success: true};
            } else {
                throw 'External request attempted for ' +
                    settings.url +
                    ', which is not defined.';
            }
        });
    };

    // Add custom Jasmine matchers.
    beforeEach(function () {
        this.addMatchers({
            toHaveAttrs: function (attrs) {
                var element = this.actual,
                    result = true;

                if ($.isEmptyObject(attrs)) {
                    return false;
                }

                $.each(attrs, function (name, value) {
                    return result = result && element.attr(name) === value;
                });

                return result;
            },
            toBeInRange: function (min, max) {
                return min <= this.actual && this.actual <= max;
            },
            toBeInArray: function (array) {
                return $.inArray(this.actual, array) > -1;
            }
        });

        return this.addMatchers(imagediff.jasmine);
    });

    // Stub jQuery.cookie module.
    $.cookie = jasmine.createSpy('jQuery.cookie').andReturn('1.0');

    // # Stub jQuery.qtip module.
    $.fn.qtip = jasmine.createSpy('jQuery.qtip');

    // Stub jQuery.scrollTo module.
    $.fn.scrollTo = jasmine.createSpy('jQuery.scrollTo');

    jasmine.initializePlayer = function (fixture, params) {
        var state;

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

        // If `params` is an object, assign it's properties as data attributes
        // to the main video DIV element.
        if (_.isObject(params)) {
            $('#example')
                .find('#video_id')
                .data(params);
        }

        jasmine.stubRequests();
        state = new Video('#example');

        state.resizer = (function () {
            var methods = [
                    'align',
                    'alignByWidthOnly',
                    'alignByHeightOnly',
                    'setParams',
                    'setMode'
                ],
                obj = {};

            $.each(methods, function (index, method) {
                obj[method] = jasmine.createSpy(method).andReturn(obj);
            });

            return obj;
        }());

        // We return the `state` object of the newly initialized Video.
        return state;
    };

    jasmine.initializePlayerYouTube = function () {
        // "video.html" contains HTML template for a YouTube video.
        return jasmine.initializePlayer('video.html');
    };
}).call(this, window.jQuery);
