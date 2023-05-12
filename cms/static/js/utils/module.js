/**
 * Utilities for modules/xblocks.
 *
 * Returns:
 *
 * urlRoot: the root for creating/updating an xblock.
 * getUpdateUrl: a utility method that returns the xblock update URL, appending
 *               the location if passed in.
 */
// eslint-disable-next-line no-undef
define(['underscore'], function(_) {
    // eslint-disable-next-line no-var
    var urlRoot = '/xblock';

    // eslint-disable-next-line no-var
    var getUpdateUrl = function(locator) {
        if (_.isUndefined(locator)) {
            return urlRoot + '/';
        } else {
            return urlRoot + '/' + locator;
        }
    };
    return {
        urlRoot: urlRoot,
        getUpdateUrl: getUpdateUrl
    };
});
