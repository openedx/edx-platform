class CMS.Views.TabsEdit extends Backbone.View
  events:
    'click .new-tab': 'addNewTab'

  initialize: =>
    @$('.component').each((idx, element) =>
        new CMS.Views.ModuleEdit(
            el: element,
            onDelete: @deleteTab,
            model: new CMS.Models.Module(
                id: $(element).data('id'),
            )
        )
    )

    @$('.components').sortable(
      handle: '.drag-handle'
      update: (event, ui) => alert 'not yet implemented!'
      helper: 'clone'
      opacity: '0.5'
      placeholder: 'component-placeholder'
      forcePlaceholderSize: true
      axis: 'y'
      items: '> .component'
    )    

  addNewTab: (event) =>
    event.preventDefault()

    editor = new CMS.Views.ModuleEdit(
      onDelete: @deleteTab
      model: new CMS.Models.Module()
    )

    $('.new-component-item').before(editor.$el)
    editor.$el.addClass('new')
    setTimeout(=>
      editor.$el.removeClass('new')
    , 500)

    editor.cloneTemplate(
      @model.get('id'),
      'i4x://edx/templates/static_tab/Empty'
    )

  deleteTab: (event) =>
    if not confirm 'Are you sure you want to delete this component? This action cannot be undone.'
      return
    $component = $(event.currentTarget).parents('.component')
    $.post('/delete_item', {
      id: $component.data('id')
    }, =>
      $component.remove()
    )




