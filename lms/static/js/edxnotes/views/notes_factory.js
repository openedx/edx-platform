;(function (define, undefined) {
'use strict';
define([
     'jquery', 'underscore', 'annotator_1.2.9', 'js/edxnotes/utils/logger',
     'js/edxnotes/views/shim', 'js/edxnotes/plugins/scroller',
     'js/edxnotes/plugins/events', 'js/edxnotes/plugins/accessibility',
     'js/edxnotes/plugins/caret_navigation'
], function ($, _, Annotator, NotesLogger) {
    var plugins = ['Auth', 'Store', 'Scroller', 'Events', 'Accessibility', 'CaretNavigation', 'Tags'],
        getOptions, setupPlugins, getAnnotator;

    /**
     * Returns options for the annotator.
     * @param {jQuery Element} The container element.
     * @param {String} params.endpoint The endpoint of the store.
     * @param {String} params.user User id of annotation owner.
     * @param {String} params.usageId Usage Id of the component.
     * @param {String} params.courseId Course id.
     * @param {String} params.token An authentication token.
     * @param {String} params.tokenUrl The URL to request the token from.
     * @return {Object} Options.
     **/
    getOptions = function (element, params) {
        var defaultParams = {
                user: params.user,
                usage_id: params.usageId,
                course_id: params.courseId
            },
            prefix = params.endpoint.replace(/(.+)\/$/, '$1');

        return {
            auth: {
                token: params.token,
                tokenUrl: params.tokenUrl
            },
            events: {
                stringLimit: params.eventStringLimit
            },
            store: {
                prefix: prefix,
                annotationData: defaultParams,
                loadFromSearch: defaultParams,
                urls: {
                    create:  '/annotations/',
                    read:    '/annotations/:id/',
                    update:  '/annotations/:id/',
                    destroy: '/annotations/:id/',
                    search:  '/search/'
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
     * @param {String} params.endpoint The endpoint of the store.
     * @param {String} params.user User id of annotation owner.
     * @param {String} params.usageId Usage Id of the component.
     * @param {String} params.courseId Course id.
     * @param {String} params.token An authentication token.
     * @param {String} params.tokenUrl The URL to request the token from.
     * @return {Object} An instance of Annotator.js.
     **/
    getAnnotator = function (element, params) {
        var el = $(element),
            options = getOptions(el, params),
            logger = NotesLogger.getLogger(element.id, params.debug),
            annotator;

        annotator = el.annotator(options).data('annotator');
        setupPlugins(annotator, plugins, options);
        annotator.logger = logger;
        logger.log({'element': element, 'options': options});
        return annotator;
    };

    return {
        factory: getAnnotator
    };
});
}).call(this, define || RequireJS.define);
