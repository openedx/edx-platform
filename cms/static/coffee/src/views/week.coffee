class CMS.Views.Week extends Backbone.View
  events:
    'click .week-edit': 'edit'

  initialize: ->
    CMS.on('content.show', @resetHeight)
    CMS.on('content.hide', @setHeight)

  render: ->
    @setHeight()
    @$('.editable').inlineEdit()
    @$('.editable-textarea').inlineEdit(control: 'textarea')
    @$('.modules .module').each ->
      new CMS.Views.Module(el: this).render()
    return @

  edit: (event) ->
    event.preventDefault()
    CMS.replaceView(new CMS.Views.WeekEdit())

  setHeight: =>
    @$el.height(@options.height)

  resetHeight: =>
    @$el.height('')
