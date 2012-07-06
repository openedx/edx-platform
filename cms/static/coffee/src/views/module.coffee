class CMS.Views.Module extends Backbone.View
  events:
    "click .module-edit": "edit"

  edit: (event) =>
    event.preventDefault()
    CMS.replaceView(new CMS.Views.ModuleEdit(model: new CMS.Models.Module(id: @$el.data('id'), type: @$el.data('type'))))
