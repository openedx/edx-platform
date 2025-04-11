/* globals AjaxPrefix */

define([
    'domReady',
    'jquery',
    'underscore',
    'underscore.string',
    'backbone',
    'gettext',
    '../../common/js/components/views/feedback_notification',
    'jquery.cookie'
], function(domReady, $, _, str, Backbone, gettext, NotificationView) {
    'use strict';

    var main, sendJSON;
    main = function() {
        AjaxPrefix.addAjaxPrefix(jQuery, function() {
            return $("meta[name='path_prefix']").attr('content');
        });
        window.CMS = window.CMS || {};
        window.CMS.URL = window.CMS.URL || {};
        window.onTouchBasedDevice = function() {
            return navigator.userAgent.match(/iPhone|iPod|iPad|Android/i);
        };
        _.extend(window.CMS, Backbone.Events);
        Backbone.emulateHTTP = true;
        $.ajaxSetup({
            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },
            dataType: 'json',
            content: {
                script: false
            }
        });
        $(document).ajaxError(function(event, jqXHR, ajaxSettings) {
            var msg, contentType,
                message = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.'); // eslint-disable-line max-len
            if (ajaxSettings.notifyOnError === false) {
                return;
            }
            contentType = jqXHR.getResponseHeader('content-type');
            if (contentType && contentType.indexOf('json') > -1 && jqXHR.responseText) {
                message = JSON.parse(jqXHR.responseText).error;
            }
            msg = new NotificationView.Error({
                title: gettext("Studio's having trouble saving your work"),
                message: message
            });
            if (window.self !== window.top) {
                try {
                    window.parent.postMessage({
                        type: 'studioAjaxError',
                        message: 'Sends a message when an AJAX error occurs',
                        payload: {}
                    }, document.referrer);
                } catch (e) {
                    console.error(e);
                }
            }
            console.log('Studio AJAX Error', { // eslint-disable-line no-console
                url: event.currentTarget.URL,
                response: jqXHR.responseText,
                status: jqXHR.status
            });
            return msg.show();
        });
        sendJSON = function(url, data, callback, type) { // eslint-disable-line no-param-reassign
            if ($.isFunction(data)) {
                callback = data;
                data = undefined;
            }
            return $.ajax({
                url: url,
                type: type,
                contentType: 'application/json; charset=utf-8',
                dataType: 'json',
                data: JSON.stringify(data),
                success: callback,
                global: data ? data.global : true // Trigger global AJAX error handler or not
            });
        };
        $.postJSON = function(url, data, callback) { // eslint-disable-line no-param-reassign
            return sendJSON(url, data, callback, 'POST');
        };
        $.patchJSON = function(url, data, callback) { // eslint-disable-line no-param-reassign
            return sendJSON(url, data, callback, 'PATCH');
        };
        return domReady(function() {
            if (window.onTouchBasedDevice()) {
                return $('body').addClass('touch-based-device');
            }
            return null;
        });
    };
    main();
    return main;
});
