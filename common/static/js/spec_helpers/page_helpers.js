define(['underscore'], function(_) {
    console.log("page_helpers.start")
    var getLocationHash;
    /**
     * Helper method that returns url hash.
     * @return {String} Returns anchor part of current url.
     */
    getLocationHash = function() {
        console.log("page_helpers.getLocationHash");
        return window.location.hash;
    };

    console.log("page_helpers.return")
    return {
        'getLocationHash': getLocationHash
    };

});
