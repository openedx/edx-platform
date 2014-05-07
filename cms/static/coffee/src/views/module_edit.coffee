define ["jquery", "underscore", "gettext", "xblock/runtime.v1",
        "js/views/xblock", "js/views/modals/edit_xblock"],
($, _, gettext, XBlock, XBlockView, EditXBlockModal) ->
  class ModuleEdit extends XBlockView
    tagName: 'li'
    className: 'component'
    editorMode: 'editor-mode'

    events:
      "click .component-actions .edit-button": 'clickEditButton'
      "click .component-actions .delete-button": 'onDelete'

    initialize: ->
      @onDelete = @options.onDelete
      @render()

    loadDisplay: ->
      XBlock.initializeBlock(@$el.find('.xblock-student_view'))

    createItem: (parent, payload, callback=->) ->
      payload.parent_locator = parent
      $.postJSON(
          @model.urlRoot + '/'
          payload
          (data) =>
              @model.set(id: data.locator)
              @$el.data('locator', data.locator)
              @$el.data('courseKey', data.courseKey)
              @render()
      ).success(callback)

    loadView: (viewName, target, callback) ->
      if @model.id
        $.ajax(
          url: "#{decodeURIComponent(@model.url())}/#{viewName}"
          type: 'GET'
          headers:
            Accept: 'application/json'
          success: (fragment) =>
            @renderXBlockFragment(fragment, target).done(callback)
        )

    render: -> @loadView('student_view', @$el, =>
      @loadDisplay()
      @delegateEvents()
    )

    clickEditButton: (event) ->
      event.preventDefault()
      modal = new EditXBlockModal({
        view: 'student_view'
      });
      modal.edit(this.$el, self.model, { refresh: _.bind(@render, this) })
