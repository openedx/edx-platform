class CMS.Views.ModuleAdd extends Backbone.View
  tagName: 'section'
  className: 'add-pane'

  events:
    'click .cancel': 'cancel'
    'click .save': 'save'

  initialize: ->
    @$el.load @model.newUrl()

  save: (event) ->
    event.preventDefault()
    @model.save({
      name: @$el.find('.name').val()
      template: $(event.target).data('template-id')
    }, {
      success: -> CMS.popView()
      error: -> alert('Create failed')
    })

  cancel: (event) ->
    event.preventDefault()
    CMS.popView()


