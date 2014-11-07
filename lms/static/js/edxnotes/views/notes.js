;(function (define, undefined) {
    'use strict';
    define([
         'jquery', 'underscore', 'annotator', 'js/edxnotes/utils/logger', 'js/edxnotes/views/shim'
    ], function ($, _, Annotator, Logger) {
        var plugins = ['Store'],
            getOptions, setupPlugins, updateHeaders, getAnnotator;

        /**
         * Returns options for the annotator.
         * @param {jQuery Element} The container element.
         * @param {String} params.endpoint The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.usageId Usage Id of the component.
         * @param {String} params.courseId Course id.
         * @return {Object} Options.
         **/
        getOptions = function (element, params) {
            var defaultParams = {
                user: params.user,
                usage_id: params.usageId,
                course_id: params.courseId
            };

            return {
                store: {
                    prefix: params.endpoint,
                    annotationData: defaultParams,
                    loadFromSearch: defaultParams
                }
            };
        };

        /**
         * Updates request headers.
         * @param {jQuery Element} The container element.
         * @param {String} token An authentication token.
         **/
        updateHeaders = function (element, token) {
            var current = element.data('annotator:headers');
            element.data('annotator:headers', $.extend(current, {
              'x-annotator-auth-token': token
            }));
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
         * @param {String} params.endpoint The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.usageId Usage Id of the component.
         * @param {String} params.courseId Course id.
         * @param {String} params.token An authentication token.
         * @return {Object} An instance of Annotator.js.
         **/
        getAnnotator = function (element, params) {
            var el = $(element),
                options = getOptions(el, params),
                annotator = el.annotator(options).data('annotator'),
                logger = new Logger(element.id, params.debug);

            setupPlugins(annotator, plugins, options);
            updateHeaders(el, params.token);
            annotator.logger = logger;
            logger.log({
                'element': element,
                'options': options,
                'annotator': annotator
            });
            return annotator;
        };

        return {
            factory: getAnnotator
        };
    });
}).call(this, define || RequireJS.define);
