define ["jquery", "jquery.ui", "backbone", "js/views/feedback_prompt", "js/views/feedback_notification",
    "coffee/src/views/module_edit", "js/models/module_info", "js/utils/module"],
($, ui, Backbone, PromptView, NotificationView, ModuleEditView, ModuleModel, ModuleUtils) ->
  class TabsEdit extends Backbone.View

    initialize: =>
      @$('.component').each((idx, element) =>
          model = new ModuleModel({
              id: $(element).data('locator')
          })

          new ModuleEditView(
              el: element,
              onDelete: @deleteTab,
              model: model
          )
      )

      @options.mast.find('.new-tab').on('click', @addNewTab)
      $('.add-pages .new-tab').on('click', @addNewTab)
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
          tabs.push($(element).data('locator'))
      )

      analytics.track "Reordered Pages",
        course: course_location_analytics

      saving = new NotificationView.Mini({title: gettext("Saving&hellip;")})
      saving.show()

      $.ajax({
        type:'POST',
        url: @model.url(),
        data: JSON.stringify({
          tabs : tabs
        }),
        contentType: 'application/json'
      }).success(=> saving.hide())

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

      analytics.track "Added Page",
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

              analytics.track "Deleted Page",
                course: course_location_analytics
                id: $component.data('locator')
              deleting = new NotificationView.Mini
                title: gettext('Deleting&hellip;')
              deleting.show()
              $.ajax({
                type: 'DELETE',
                url: ModuleUtils.getUpdateUrl($component.data('locator'))
              }).success(=>
                $component.remove()
                deleting.hide()
              )
          secondary: [
            text: gettext('Cancel')
            click: (view) ->
              view.hide()
          ]
      confirm.show()
