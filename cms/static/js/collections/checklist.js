define(["backbone", "underscore", "js/models/checklist"],
        function(Backbone, _, ChecklistModel) {
    var ChecklistCollection = Backbone.Collection.extend({
        model : ChecklistModel,

        parse: function(response) {
            _.each(response,
                function( element, idx ) {
                    element.id = idx;
                });

            return response;
        },

        // Disable caching so the browser back button will work (checklists have links to other
        // places within Studio).
        fetch: function (options) {
            options.cache = false;
            return Backbone.Collection.prototype.fetch.call(this, options);
        }
    });
    return ChecklistCollection;
});
