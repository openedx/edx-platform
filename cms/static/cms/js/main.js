/* globals AjaxPrefix */

(function(AjaxPrefix) {
    'use strict';
    define(['domReady', 'jquery', 'underscore.string', 'backbone', 'gettext',
            'common/js/components/views/feedback_notification', 'coffee/src/ajax_prefix',
            'jquery.cookie'],
    function(domReady, $, str, Backbone, gettext, NotificationView) {
        var main;
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
                dataType: 'json'
            });
            $(document).ajaxError(function(event, jqXHR, ajaxSettings) {
                var msg, contentType,
                    message = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.');  // eslint-disable-line max-len
                if (ajaxSettings.notifyOnError === false) {
                    return;
                }
                contentType = jqXHR.getResponseHeader('content-type');
                if (contentType && contentType.indexOf('json') > -1 && jqXHR.responseText) {
                    message = JSON.parse(jqXHR.responseText).error;
                }
                msg = new NotificationView.Error({
                    'title': gettext("Studio's having trouble saving your work"),
                    'message': message
                });
                console.log('Studio AJAX Error', { // eslint-disable-line no-console
                    url: event.currentTarget.URL,
                    response: jqXHR.responseText,
                    status: jqXHR.status
                });
                return msg.show();
            });
            $.postJSON = function(url, data, callback, type) {
                if ($.isFunction(data)) {
                    callback = data;
                    data = undefined;
                }
                type = type || 'POST';
                return $.ajax({
                    url: url,
                    type: type,
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json',
                    data: JSON.stringify(data),
                    success: callback
                });
            };
            return domReady(function() {
                if (window.onTouchBasedDevice()) {
                    return $('body').addClass('touch-based-device');
                }
            });
        };
        main();
        return main;
    });
}).call(this, AjaxPrefix);
