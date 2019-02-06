/* global _ */

(function() {
    'use strict';
    var origAjax = $.ajax;

    jasmine.stubRequests = function() {
        var spy = $.ajax;
        if (!jasmine.isSpy($.ajax)) {
            spy = spyOn($, 'ajax');
        }

        return spy.and.callFake(function(settings) {
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
                return settings.success(jasmine.stubbedCaption);
            } else if (settings.url === '/transcript/available_translations') {
                return settings.success(['uk', 'de']);
            } else if (settings.url.match(/.+\/problem_get$/)) {
                return settings.success({
                    html: window.readFixtures('common/js/fixtures/problem_content.html')
                });
            } else if (
                settings.url === '/calculate' ||
                settings.url.match(/.+\/goto_position$/) ||
                settings.url.match(/event$/) ||
                settings.url.match(/.+\/problem_(check|reset|show|save)$/)
            ) {
                // Do nothing.
                return {};
            } else if (settings.url === '/save_user_state') {
                return {success: true};
            } else if (settings.url.match(new RegExp(jasmine.getFixtures().fixturesPath + '.+', 'g'))) {
                return origAjax(settings);
            } else {
                return $.ajax.and.callThrough();
            }
        });
    };
}).call(this);
