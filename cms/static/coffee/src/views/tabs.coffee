define ["jquery", "jquery.ui", "backbone", "js/views/feedback_prompt", "js/views/feedback_notification", "coffee/src/models/module", "coffee/src/views/module_edit"],
($, ui, Backbone, PromptView, NotificationView, ModuleModel, ModuleEditView) ->
  class TabsEdit extends Backbone.View

    initialize: =>
      @$('.component').each((idx, element) =>
          new ModuleEditView(
              el: element,
              onDelete: @deleteTab,
              model: new ModuleModel(
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

      editor = new ModuleEditView(
        onDelete: @deleteTab
        model: new ModuleModel()
      )

      $('.new-component-item').before(editor.$el)
      editor.$el.addClass('new')
      setTimeout(=>
        editor.$el.removeClass('new')
      , 500)

      editor.createItem(
        @model.get('id'),
        {category: 'static_tab'}
      )

      analytics.track "Added Static Page",
        course: course_location_analytics

    deleteTab: (event) =>
      confirm = new PromptView.Warning
        title: gettext('Delete Component Confirmation')
        message: gettext('Are you sure you want to delete this component? This action cannot be undone.')
        actions:
          primary:
            text: gettext("OK")
            click: (view) ->
              view.hide()
              $component = $(event.currentTarget).parents('.component')

              analytics.track "Deleted Static Page",
                course: course_location_analytics
                id: $component.data('id')
              deleting = new NotificationView.Mini
                title: gettext('Deleting&hellip;')
              deleting.show()
              $.post('/delete_item', {
                id: $component.data('id')
              }, =>
                $component.remove()
                deleting.hide()
              )
          secondary: [
            text: gettext('Cancel')
            click: (view) ->
              view.hide()
          ]
      confirm.show()
