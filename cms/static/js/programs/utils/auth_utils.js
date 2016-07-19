define([
        'jquery',
        'underscore',
        'js/programs/utils/api_config'
    ],
    function( $, _, apiConfig ) {
        'use strict';

        var auth = {
            autoSync: {
                /**
                 * Override Backbone.sync to seamlessly attempt (re-)authentication when necessary.
                 *
                 * If a 401 error response is encountered while making a request to the Programs,
                 * API, this wrapper will attempt to request an id token from a custom endpoint
                 * via AJAX.  Then the original request will be retried once more.
                 *
                 * Any other response than 401 on the original API request, or any error occurring
                 * on the retried API request (including 401), will be handled by the base sync
                 * implementation.
                 *
                 */
                sync: function( method, model, options ) {

                    var oldError = options.error;

                    this._setHeaders( options );

                    options.notifyOnError = false;  // suppress Studio error pop-up that will happen if we get a 401

                    options.error = function(xhr, textStatus, errorThrown) {
                        if (xhr && xhr.status === 401) {
                            // attempt auth and retry
                            this._updateToken(function() {
                                // restore the original error handler
                                options.error = oldError;
                                options.notifyOnError = true;  // if it fails again, let Studio notify.
                                delete options.xhr;  // remove the failed (401) xhr from the last try.

                                // update authorization header
                                this._setHeaders( options );

                                Backbone.sync.call(this, method, model, options);
                            }.bind(this));
                        } else if (oldError) {
                            // fall back to the original error handler
                            oldError.call(this, xhr, textStatus, errorThrown);
                        }
                    }.bind(this);
                    return Backbone.sync.call(this, method, model, options);
                },

                /**
                 * Fix up headers on an imminent AJAX sync, ensuring that the JWT token is enclosed
                 * and that credentials are included when the request is being made cross-domain.
                 */
                _setHeaders: function( ajaxOptions ) {
                    ajaxOptions.headers = _.extend ( ajaxOptions.headers || {}, {
                        Authorization: 'JWT ' + apiConfig.get( 'idToken' )
                    });
                    ajaxOptions.xhrFields = _.extend( ajaxOptions.xhrFields || {}, {
                        withCredentials: true
                    });
                },

                /**
                 * Fetch a new id token from the configured endpoint, update the api config,
                 * and invoke the specified callback.
                 */
                _updateToken: function( success ) {

                    $.ajax({
                        url: apiConfig.get('authUrl'),
                        xhrFields: {
                            // See: https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/withCredentials
                            withCredentials: true
                        },
                        crossDomain: true
                    }).done(function ( data ) {
                        // save the newly-retrieved id token
                        apiConfig.set( 'idToken', data.id_token );
                    }).done( success );
                }
            }
        };

        return auth;
    }
);
