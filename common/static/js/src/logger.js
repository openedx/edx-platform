;(function() {
    'use strict';
    var Logger = (function() {
        // listeners[event_type][element] -> list of callbacks
        var listeners = {},
            sendRequest, has;

        sendRequest = function(data, options) {
            var request = $.ajaxWithPrefix ? $.ajaxWithPrefix : $.ajax;

            options = $.extend(true, {
                'url': '/event',
                'type': 'POST',
                'data': data,
                'async': true
            }, options);
            return request(options);
        };

        has = function(object, propertyName) {
            return {}.hasOwnProperty.call(object, propertyName);
        };

        return {
            /**
             * Emits an event.
             *
             * Note that this method is used by external XBlocks, and the API cannot change without
             * proper deprecation and notification for external authors.
             */
            log: function(eventType, data, element, requestOptions) {
                var callbacks;

                if (!element) {
                    // null element in the listener dictionary means any element will do.
                    // null element in the Logger.log call means we don't know the element name.
                    element = null;
                }
                // Check to see if we're listening for the event type.
                if (has(listeners, eventType)) {
                    if (has(listeners[eventType], element)) {
                        // Make the callbacks.
                        callbacks = listeners[eventType][element];
                        $.each(callbacks, function(index, callback) {
                            try {
                                callback(eventType, data, element);
                            } catch (err) {
                                console.error({
                                    eventType: eventType,
                                    data: data,
                                    element: element,
                                    error: err
                                });
                            }
                        });
                    }
                }
                // Regardless of whether any callbacks were made, log this event.
                return sendRequest({
                    'event_type': eventType,
                    'event': JSON.stringify(data),
                    'page': window.location.href
                }, requestOptions);
            },

            /**
             * Adds a listener. If you want any element to trigger this listener,
             * do element = null.
             *
             * Note that this method is used by external XBlocks, and the API cannot change without
             * proper deprecation and notification for external authors.
             */
            listen: function(eventType, element, callback) {
                listeners[eventType] = listeners[eventType] || {};
                listeners[eventType][element] = listeners[eventType][element] || [];
                listeners[eventType][element].push(callback);
            },

            /**
             * Binds `page_close` event.
             *
             * Note that this method is used by external XBlocks, and the API cannot change without
             * proper deprecation and notification for external authors.
             */
            bind: function() {
                window.onunload = function() {
                    sendRequest({
                        event_type: 'page_close',
                        event: '',
                        page: window.location.href
                    }, {type: 'GET', async: false});
                };
            }
        };
    }());

    this.Logger = Logger;
    // log_event exists for compatibility reasons and will soon be deprecated.
    this.log_event = Logger.log;
}).call(this);
