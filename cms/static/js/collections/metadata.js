define(["backbone", "js/models/metadata"], function(Backbone, MetadataModel) {
    var MetadataCollection = Backbone.Collection.extend({
        model : MetadataModel,
        comparator: "display_name"
    });
    return MetadataCollection;
});
