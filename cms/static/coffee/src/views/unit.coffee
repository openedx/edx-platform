class CMS.Views.UnitEdit extends Backbone.View
  events:
    'click .new-component .new-component-type a': 'showComponentTemplates'
    'click .new-component .cancel-button': 'closeNewComponent'
    'click .new-component-templates .new-component-template a': 'saveNewComponent'
    'click .new-component-templates .cancel-button': 'closeNewComponent'
    'click .new-component-button': 'showNewComponentForm'
    'click .unit-actions .save-button': 'save'

  initialize: =>
    @$newComponentItem = @$('.new-component-item')
    @$newComponentTypePicker = @$('.new-component')
    @$newComponentTemplatePickers = @$('.new-component-templates')
    @$newComponentButton = @$('.new-component-button')

    @$('.components').sortable(
      handle: '.drag-handle'
      update: (event, ui) => @saveOrder()
    )

    @$('.component').each((idx, element) ->
        new CMS.Views.ModuleEdit(
            el: element,
            model: new CMS.Models.Module(
                id: $(element).data('id'),
            )
        )
    )

    @model.components = @components()

  showNewComponentForm: (event) =>
    event.preventDefault()
    @$newComponentItem.addClass('adding')
    $(event.target).slideUp(150)
    @$newComponentTypePicker.slideDown(250)

  showComponentTemplates: (event) =>
    event.preventDefault()

    type = $(event.currentTarget).data('type')
    @$newComponentTypePicker.slideUp(250)
    @$(".new-component-#{type}").slideDown(250)

  closeNewComponent: (event) =>
    event.preventDefault()

    @$newComponentTypePicker.slideUp(250)
    @$newComponentTemplatePickers.slideUp(250)
    @$newComponentButton.slideDown(250)
    @$newComponentItem.removeClass('adding')
    @$newComponentItem.find('.rendered-component').remove()

  saveNewComponent: (event) =>
    event.preventDefault()

    editor = new CMS.Views.ModuleEdit(
      model: new CMS.Models.Module()
    )

    @$newComponentItem.before(editor.$el)

    editor.cloneTemplate($(event.currentTarget).data('location'))

    @closeNewComponent(event)

  components: => @$('.component').map((idx, el) -> $(el).data('id')).get()

  saveOrder: =>
    @model.save(
      children: @components()
    )
