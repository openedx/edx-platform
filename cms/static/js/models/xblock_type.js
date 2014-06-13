define(["backbone", "js/utils/module"], function(Backbone, ModuleUtils) {
    var XBlockType = Backbone.Model.extend({

        urlRoot: ModuleUtils.urlRoot,

        defaults: {
            "id": null,
            "display_name": null,
            "publish_status": "Unknown",
            "locators": [],
            "studio_url": null
        },

        parse: function (response) {
            this.id = response.id;
            this.displayName = response.display_name;
            this.locators = response.locators;
            this.studioUrl = response.studio_url;
        }

    });
    return XBlockType;
});
