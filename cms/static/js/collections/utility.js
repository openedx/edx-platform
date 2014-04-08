define(["backbone", "underscore", "js/models/utility"],
        function(Backbone, _, UtilityModel) {
    var UtilityCollection = Backbone.Collection.extend({
        model : UtilityModel,

        parse: function(response) {
            _.each(response,
                function( element, idx ) {
                    element.id = idx;
                });

            return response;
        },

        // Disable caching so the browser back button will work (utilities have links to other
        // places within Studio).
        fetch: function (options) {
            options.cache = false;
            return Backbone.Collection.prototype.fetch.call(this, options);
        }
    });
    return UtilityCollection;
});
