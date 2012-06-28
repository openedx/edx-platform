class CMS.Views.Module extends Backbone.View
  events:
    "click .module-edit": "edit"

  initialize: ->
    @model = new CMS.Models.Module(id: @$el.data('id'), type: @$el.data('type'))

  edit: =>
    CMS.replaceView(new CMS.Views.ModuleEdit(model: @model))
