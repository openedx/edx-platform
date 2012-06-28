class CMS.Views.Module extends Backbone.View
  events:
    "click .module-edit": "edit"

  initialize: ->
    @model = new CMS.Models.Module(id: @el.id)

  edit: =>
    CMS.trigger('showContent', new CMS.Views.ModuleEdit(model: @model))
