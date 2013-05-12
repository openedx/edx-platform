if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.String = Backbone.View.extend({

    // Model class ...
    events : {
    },

    initialize : function() {
        var self = this;
        this.uniqueId = _.uniqueId('metadata_string_entry_');
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("metadata_string_entry",
            "/static/client_templates/metadata_string_entry.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({model: self.model, uniqueId: self.uniqueId}));
                if (self.model.get('explicitly_set')) {
                    self.$el.addClass('is-set');
                    self.$el.find('#'+self.uniqueId + " .setting-clear").addClass('active');
                }
            }
        );
    },

    modified: function () {
       return this.getValue() !== this.model.getOriginalValue();
    },

    getValue: function() {
        return this.$el.find('#' + this.uniqueId).val();
    }
});
