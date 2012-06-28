class CMS.Views.Week extends Backbone.View
  events:
    'click .module-edit': 'edit'

  initialize: ->
    @model = new CMS.Models.Week(id: @$el.data('id'))
    @setHeight()
    @$('.editable').inlineEdit()
    @$('.editable-textarea').inlineEdit(control: 'textarea')

    @$('.modules .module').each ->
      new CMS.Views.Module el: this

    CMS.on('content.show', @resetHeight)
    CMS.on('content.hide', @setHeight)

  edit: =>
    CMS.replaceView(new CMS.Views.WeekEdit(model: @model))

  setHeight: =>
    @$el.height(@options.height)

  resetHeight: =>
    @$el.height('')
