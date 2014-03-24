define(["backbone", "js/utils/module"], function(Backbone, ModuleUtils) {
    var XBlockInfo = Backbone.Model.extend({

        urlRoot: ModuleUtils.urlRoot,

        defaults: {
            "id": null,
            "display_name": null,
            "category": null,
            "is_draft": null,
            "is_container": null,
            "children": []
        }
    });
    return XBlockInfo;
});