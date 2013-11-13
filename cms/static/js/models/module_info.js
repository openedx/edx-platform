define(["backbone"], function(Backbone) {
    var ModuleInfo = Backbone.Model.extend({
      urlRoot: "/xblock",

      defaults: {
        "id": null,
        "data": null,
        "metadata" : null,
        "children" : null
      }
    });
    return ModuleInfo;
});
