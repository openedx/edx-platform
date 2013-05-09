if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Generic = Backbone.View.extend({

    // Model class ...
    events : {
    },

    initialize : function() {
        var self = this;
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("metadata_entry",
            "/static/client_templates/generic_metadata_entry.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({model: self.model}));
            }
        );
    },

    modified: function () {
       return this.getValue() !== this.model.getOriginalValue();
    },

    getValue: function() {
        return this.$el.find('.editor').val();
    }
});
