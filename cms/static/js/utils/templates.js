// eslint-disable-next-line no-undef
define(['jquery', 'underscore'], function($, _) {
    /**
     * Loads the named template from the page, or logs an error if it fails.
     * @param name The name of the template.
     * @returns The loaded template.
     */
    // eslint-disable-next-line no-var
    var loadTemplate = function(name) {
        // eslint-disable-next-line no-var
        var templateSelector = '#' + name + '-tpl',
            templateText = $(templateSelector).text();
        if (!templateText) {
            // eslint-disable-next-line no-console
            console.error('Failed to load ' + name + ' template');
        }
        return _.template(templateText);
    };

    return {
        loadTemplate: loadTemplate
    };
});
