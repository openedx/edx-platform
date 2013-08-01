CMS.Models.Course = Backbone.Model.extend({
    defaults: {
        "name": ""
    },
    validate: function(attrs, options) {
        if (!attrs.name) {
            return gettext("You must specify a name");
        }
    }
});
