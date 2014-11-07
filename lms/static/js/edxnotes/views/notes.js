;(function (define, $, _, undefined) {
    'use strict';
    define([
        'annotator', 'js/edxnotes/utils/logger', 'js/edxnotes/views/shim'
    ], function (Annotator, Logger) {
        var plugins = ['Store'],
            getOptions, setupPlugins, getAnnotator;

        /**
         * Returns options for the annotator.
         * @param {jQuery Element} The container element.
         * @param {String} params.endpoint The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.usageId Usage Id of the component.
         * @param {String} params.courseId Course id.
         * @param {String} params.token An authentication token.
         * @return {Object} Options.
         **/
        getOptions = function (element, params) {
            var defaultParams = {
                token: params.token,
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
}).call(this, define || RequireJS.define, jQuery, _);
