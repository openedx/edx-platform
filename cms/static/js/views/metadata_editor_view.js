if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Editor = Backbone.View.extend({

    // Model class is ...
    events : {
    },

    views : {}, // child views

    initialize : function() {
        var self = this;
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("metadata_editor",
            "/static/client_templates/metadata_editor.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({metadata_entries: self.model.attributes}));
                var counter = 0;
                _.each(self.model.attributes,
                    function(item, key) {
                        self.views[key] = new CMS.Views.Metadata.Generic({
                                el: self.$el.find('.metadata_entry')[counter],
                                model: new CMS.Models.Metadata(item)
                            }
                        );
                        counter+=1;
                    });
            }
        );
    },

    getModifiedMetadataValues: function () {
        var modified_values = {};
        _.each(this.views,
            function (item, key) {
                if (item.modified()) {
                    modified_values[key] = item.getValue();
                }
            }
        );
        return modified_values;
    }
});
