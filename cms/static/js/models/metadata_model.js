CMS.Models.Metadata = Backbone.Model.extend({
    // This model class is not suited for restful operations and is considered just a server side initialized container
    url: '',

    defaults: {
        "display_name": null,
        "value" : null
    },

    getOriginalValue: function() {
        return this.get('value');
    }
});
