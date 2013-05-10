if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Option = Backbone.View.extend({

    // Model class ...
    events : {
    },

    initialize : function() {
        var self = this;
        this.uniqueId = _.uniqueId('metadata_option_entry_');
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("metadata_option_entry",
            "/static/client_templates/metadata_option_entry.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({model: self.model, uniqueId: self.uniqueId}));
                $('#' + self.uniqueId + " option").filter(function() {
                    return $(this).text() === self.model.get('value');
                }).prop('selected', true);
            }
        );
    },

    modified: function () {
        return this.getValue() !== this.model.getOriginalValue();
    },

    getValue: function() {
        return this.$el.find('#' + this.uniqueId).find(":selected").text();
    }
});
