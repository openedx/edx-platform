(function (define, $, _, Annotator, undefined) {
    'use strict';
    define('edxnotes/notes.js', ['edxnotes/plugins/accessability'], function () {
        var getUri, getUsageId, getOptions, setupPlugins, getAnnotator;
        /**
         * Returns current URI for the page.
         * @return {String} URI.
         **/
        getUri = function () {
            return window.location.href.replace(/\?.*|\#.*/g, '');
        };

        /**
         * Returns Usage id for the component.
         * @param {jQuery Element} The container element.
         * @return {String} Usage id.
         **/
        getUsageId = function (element) {
            return element.closest('[data-usage-id]').data('usage-id');
        };

        /**
         * Returns options for the annotator.
         * @param {jQuery Element} The container element.
         * @param {String} params.token An auth token.
         * @param {String} params.prefix The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.tokenUrl The URL on the local server to request an authentication token.
         * @return {Object} Options.
         **/
        getOptions = function (element, params) {
            var uri = getUri(),
                usageId = getUsageId(element);

            return {
                permissions: {
                    user: params.user,
                    permissions: {
                        'read':   [params.user],
                        'update': [params.user],
                        'delete': [params.user],
                        'admin':  [params.user]
                    },
                    showViewPermissionsCheckbox: false,
                    showEditPermissionsCheckbox: false,
                },
                auth: {
                    token: params.token,
                    tokenUrl: params.tokenUrl
                },
                store: {
                    prefix: params.prefix,
                    annotationData: {
                        user: params.user,
                        usage_id: usageId
                    },
                    loadFromSearch: {
                        user: params.user,
                        usage_id: usageId
                    }
                }
            };
        };

        /**
         * Setups plugins for the annotator.
         * @param {Object} annotator An instance of the annotator.
         * @param {Array} plugins A list of plugins for the annotator.
         * @param {Object} options An options for the annotator.
         **/
        setupPlugins = function (annotator, plugins, options) {
            _.each(plugins, function(plugin) {
                var settings = options[plugin.toLowerCase()];
                annotator.addPlugin(plugin, settings);
            }, this);
        };

        /**
         * Factory method that returns Annotator.js instantiates.
         * @param {DOM Element} element The container element.
         * @param {String} params.token An auth token.
         * @param {String} params.prefix The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.tokenUrl The URL on the local server to request an authentication token.
         * @return {Object} An instance of Annotator.js.
         **/
        getAnnotator = function (element, params) {
            var element = $(element),
                options = getOptions(element, params),
                annotator = element.annotator(options).data('annotator'),
                plugins = ['Auth', 'Permissions', 'Store'];

            setupPlugins(annotator, plugins, options);
            return annotator;
        };

        return {
            factory: getAnnotator
        };
    });
}).call(this, RequireJS.define, jQuery, _, Annotator);
