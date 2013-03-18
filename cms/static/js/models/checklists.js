CMS.Models.Checklist = Backbone.Model.extend({
});

CMS.Models.ChecklistCollection = Backbone.Collection.extend({
    model : CMS.Models.Checklist,

    parse: function(response) {
        _.each(response,
            function( element, idx ) {
                element.id = idx;
            });

        return response;
    }
});

