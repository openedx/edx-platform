(function () {
    'use strict';
    var origAjax = $.ajax;

    var stubbedYT = {
        Player: function () {
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
        ready: function (f) {
            return f();
        }
    };
    jasmine.YT = stubbedYT;
    // Stub YouTube API.
    window.YT = stubbedYT;

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
            contentDetails : {
                id: '7tqY6eQzVhE',
                duration: 'PT5M0S'
            }
        },
        'cogebirgzzM': {
            contentDetails : {
                id: 'cogebirgzzM',
                duration: 'PT3M20S'
            }
        },
        'abcdefghijkl': {
            contentDetails : {
                id: 'abcdefghijkl',
                duration: 'PT6M40S'
            }
        },
        bogus: {
            contentDetails : {
                duration: 'PT1M40S'
            }
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
        if (!jasmine.isSpy($.ajax)) {
            spy = spyOn($, 'ajax');
        }

        return spy.and.callFake(function (settings) {
            var match = settings.url
                    .match(/googleapis\.com\/.+\/videos\/\?id=(.+)&part=contentDetails/),
                status, callCallback;
            if (match) {
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
                        items: jasmine.stubbedMetadata[match[1]]
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
            } else if (settings.url.match(/transcript\/translation\/.+$/)) {
                return settings.success(jasmine.stubbedCaption);
            } else if (settings.url === '/transcript/available_translations') {
                return settings.success(['uk', 'de']);
            } else if (settings.url.match(/.+\/problem_get$/)) {
                return settings.success({
                    html: window.readFixtures('problem_content.html')
                });
            } else if (
                settings.url === '/calculate' ||
                settings.url.match(/.+\/goto_position$/) ||
                settings.url.match(/event$/) ||
                settings.url.match(/.+\/problem_(check|reset|show|save)$/)
            ) {
                // Do nothing.
                return;
            } else if (settings.url === '/save_user_state') {
                return {success: true};
            } else if(settings.url.match(new RegExp(jasmine.getFixtures().fixturesPath + ".+", 'g'))) {
                return origAjax(settings);
            } else {
                $.ajax.and.callThrough();
            }
        });
    };

   // Stub jQuery.cookie module.
    $.cookie = jasmine.createSpy('jQuery.cookie').and.returnValue('1.0');

    // # Stub jQuery.qtip module.
    $.fn.qtip = jasmine.createSpy('jQuery.qtip');

    // Stub jQuery.scrollTo module.
    $.fn.scrollTo = jasmine.createSpy('jQuery.scrollTo');

    // Stub window.Video.loadYouTubeIFrameAPI()
    window.Video.loadYouTubeIFrameAPI = jasmine.createSpy('window.Video.loadYouTubeIFrameAPI').and.returnValue(
        function (scriptTag) {
            var event = document.createEvent('Event');
            if (fixture === "video.html") {
                event.initEvent('load', false, false);
            } else {
                event.initEvent('error', false, false);
            }
            scriptTag.dispatchEvent(event);
        }
    );

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

        // If `params` is an object, assign its properties as data attributes
        // to the main video DIV element.
        if (_.isObject(params)) {
            var metadata = _.extend($('#video_id').data('metadata'), params);
            $('#video_id').data('metadata', metadata);
        }

        jasmine.stubRequests();
        state = new window.Video('#example');

        state.resizer = (function () {
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
                    add: jasmine.createSpy().and.returnValue(obj),
                    substract: jasmine.createSpy().and.returnValue(obj),
                    reset: jasmine.createSpy().and.returnValue(obj)
                };

            $.each(methods, function (index, method) {
                obj[method] = jasmine.createSpy(method).and.returnValue(obj);
            });

            obj.delta = delta;

            return obj;
        }());

        // We return the `state` object of the newly initialized Video.
        return state;
    };

    jasmine.initializePlayerYouTube = function (params) {
        // "video.html" contains HTML template for a YouTube video.
        return jasmine.initializePlayer('video.html', params);
    };
}).call(this);
