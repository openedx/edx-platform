CMS.Models.ModuleInfo = Backbone.Model.extend({
  url: function() {return "/module_info/" + this.id;},

  defaults: {
    "id": null,
    "data": null,
    "metadata" : null,
    "children" : null
  }
});
