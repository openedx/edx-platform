;(function (define, $, _, undefined) {
    'use strict';
    define([
        'annotator', 'js/edxnotes/logger', 'js/edxnotes/shim'
    ], function (Annotator, Logger) {
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
         * Returns course id for the component.
         * @param {jQuery Element} The container element.
         * @return {String} Course id.
         **/
        getCourseId = function (element) {
            return element.closest('[data-course-id]').data('course-id');
        };

        /**
         * Returns options for the annotator.
         * @param {jQuery Element} The container element.
         * @param {String} params.prefix The endpoint of the store.
         * @param {String} params.user User id of annotation owner.
         * @param {String} params.username Username of annotation owner.
         * @param {String} params.usageId Usage Id of the component.
         * @param {String} params.courseId Course id.
         * @return {Object} Options.
         **/
        getOptions = function (element, params) {
            var usageId = params.usageId || getUsageId(element),
                courseId = params.courseId || getCourseId(element),
                defaultParams = {
                    user: params.user,
                    usage_id: usageId,
                    username: params.username,
                    course_id: courseId
                };

            return {
                store: {
                    prefix: params.prefix,
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
                plugins = ['Store'],
                logger = new Logger(element.id, params.debug);

            annotator.logger = logger;
            el.data('annotator', annotator);
            setupPlugins(annotator, plugins, options);
            logger.log({
                'constructor': Annotator,
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
