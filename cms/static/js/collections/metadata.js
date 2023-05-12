// eslint-disable-next-line no-undef
define(['backbone', 'js/models/metadata'], function(Backbone, MetadataModel) {
    // eslint-disable-next-line no-var
    var MetadataCollection = Backbone.Collection.extend({
        model: MetadataModel,
        comparator: 'display_name'
    });
    return MetadataCollection;
});
