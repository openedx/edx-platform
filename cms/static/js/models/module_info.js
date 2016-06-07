define(["backbone", "js/utils/module"], function(Backbone, ModuleUtils) {
    var ModuleInfo = Backbone.Model.extend({
      urlRoot: ModuleUtils.urlRoot,

      defaults: {
        "id": null,
        "data": null,
        "metadata" : null,
        "children" : null
      }
    });
    return ModuleInfo;
});
