class CMS.Views.Week extends Backbone.View
  events:
    'click .module-edit': 'edit'

  initialize: ->
    @model = new CMS.Models.Week(id: @el.id)
    @$el.height @options.height
    @$('.editable').inlineEdit()
    @$('.editable-textarea').inlineEdit(control: 'textarea')

    @$('#modules .module').each ->
      new CMS.Views.Module el: this

  edit: =>
    CMS.trigger('showContent', new CMS.Views.WeekEdit(model: @model))
