(function (define, $, _, undefined) {
    'use strict';
    define(['annotator', 'js/edxnotes/plugins/accessibility'], function (Annotator) {
        var getUsageId, getOptions, setupPlugins, getAnnotator;
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
         * @param {String} params.tokenUrl The URL on the local server to request an authentication token.
         * @param {String} params.prefix The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.usageId Usage Id of the component.
         * @param {String} params.courseId Course id.
         * @return {Object} Options.
         **/
        getOptions = function (element, params) {
            var usageId = params.usageId || getUsageId(element);
            return {
                auth: {
                    token: params.token,
                    tokenUrl: params.tokenUrl
                },
                store: {
                    prefix: params.prefix,
                    annotationData: {
                        user: params.user,
                        usage_id: usageId,
                        course_id: params.courseId
                    },
                    loadFromSearch: {
                        user: params.user,
                        usage_id: usageId,
                        course_id: params.courseId
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
         * @param {String} params.tokenUrl The URL on the local server to request an authentication token.
         * @param {String} params.prefix The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.usageId Usage Id of the component.
         * @param {String} params.courseId Course id.
         * @return {Object} An instance of Annotator.js.
         **/
        getAnnotator = function (element, params) {
            var el = $(element),
                options = getOptions(el, params),
                annotator = new Annotator(element, options),
                plugins = [/*'Auth', */'Store'];

            el.data('annotator', annotator);
            setupPlugins(annotator, plugins, options);
            return annotator;
        };

        return {
            factory: getAnnotator
        };
    });
}).call(this, RequireJS.define, jQuery, _);
