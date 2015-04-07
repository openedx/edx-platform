define(['underscore'], function(_) {
    var getLocationHash;
    /**
     * Helper method that returns url hash.
     * @return {String} Returns anchor part of current url.
     */
    getLocationHash = function() {
        return window.location.hash;
    };

    return {
        'getLocationHash': getLocationHash
    };

});
