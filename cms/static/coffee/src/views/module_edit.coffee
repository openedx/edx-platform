class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  initialize: ->
    CMS.trigger 'module.edit'
    @$el.append($('<div id="module-html">').load(@model.editUrl()))
