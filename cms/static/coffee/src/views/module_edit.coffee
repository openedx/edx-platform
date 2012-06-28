class CMS.Views.ModuleEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  events:
    'click .cancel': 'cancel'
    # 'click .module-edit', 'edit'

  initialize: ->
    @$el.append($("""<div id="#{@model.get('id')}">""").load(@model.editUrl()))

  cancel: ->
    CMS.popView()
