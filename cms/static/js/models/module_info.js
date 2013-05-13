CMS.Models.ModuleInfo = Backbone.Model.extend({
  url: function() {
    return "/" + this.get('courseId') + "/module_info/" + this.id;
  },

  defaults: {
    "id": null,
    "data": null,
    "metadata" : null,
    "children" : null
  }
});
