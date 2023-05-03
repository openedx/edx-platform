(function(define, undefined) {
    'use strict';

    define(['annotator_1.2.9'], function(Annotator) {
    /**
     * Modifies Annotator.Plugin.Store.prototype._onError to show custom error message
     * if sent by server
     */
        var originalErrorHandler = Annotator.Plugin.Store.prototype._onError;
        Annotator.Plugin.Store.prototype._onError = function(xhr) {
            var serverResponse;

            // Try to parse json
            if (xhr.responseText) {
                try {
                    serverResponse = JSON.parse(xhr.responseText);
                } catch (exception) {
                    serverResponse = null;
                }
            }

            // if response includes an error message it will take precedence
            if (serverResponse && serverResponse.error_msg) {
                Annotator.showNotification(serverResponse.error_msg, Annotator.Notification.ERROR);
                return console.error(Annotator._t('API request failed:') + (" '" + xhr.status + "'"));
            }

            // Delegate to original error handler
            originalErrorHandler(xhr);
        };
    });
}).call(this, define || RequireJS.define);

