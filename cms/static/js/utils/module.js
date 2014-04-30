/**
 * Utilities for modules/xblocks.
 *
 * Returns:
 *
 * urlRoot: the root for creating/updating an xblock.
 * getUpdateUrl: a utility method that returns the xblock update URL, appending
 *               the location if passed in.
 */
define([], function () {
    var urlRoot = '/xblock';

    var getUpdateUrl = function (locator) {
        if (locator === undefined) {
            return urlRoot + "/";
        }
        else {
            return urlRoot + "/" + locator;
        }
    };
    return {
        urlRoot: urlRoot,
        getUpdateUrl: getUpdateUrl
    };
});

