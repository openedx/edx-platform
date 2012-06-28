class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  events:
    'click .cancel': 'cancel'
    'click .module-edit': 'editSubmodule'

  initialize: ->
    @$el.append($("""<div id="#{@model.get('id')}">""").load(@model.editUrl()))

  cancel: ->
    CMS.popView()

  editSubmodule: (event) =>
    $el = $(event.target)
    model = new CMS.Models.Module(id: $el.data('id'), type: $el.data('type'))
    CMS.pushView(new CMS.Views.ModuleEdit(model: model))
