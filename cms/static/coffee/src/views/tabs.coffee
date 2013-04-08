class CMS.Views.TabsEdit extends Backbone.View

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

    @options.mast.find('.new-tab').on('click', @addNewTab)
    @$('.components').sortable(
      handle: '.drag-handle'
      update: @tabMoved
      helper: 'clone'
      opacity: '0.5'
      placeholder: 'component-placeholder'
      forcePlaceholderSize: true
      axis: 'y'
      items: '> .component'
    )    

  tabMoved: (event, ui) =>
    tabs = []
    @$('.component').each((idx, element) =>
        tabs.push($(element).data('id'))
    )

    analytics.track "Reordered Static Pages",
      course: course_location_analytics

    $.ajax({
      type:'POST',
      url: '/reorder_static_tabs', 
      data: JSON.stringify({
        tabs : tabs
      }),
      contentType: 'application/json'
    })

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

    analytics.track "Added Static Page",
      course: course_location_analytics

  deleteTab: (event) =>
    if not confirm 'Are you sure you want to delete this component? This action cannot be undone.'
      return
    $component = $(event.currentTarget).parents('.component')

    analytics.track "Deleted Static Page",
      course: course_location_analytics
      id: $component.data('id')

    $.post('/delete_item', {
      id: $component.data('id')
    }, =>
      $component.remove()
    )




