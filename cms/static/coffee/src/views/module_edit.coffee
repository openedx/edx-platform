define ["jquery", "underscore", "gettext", "xblock/runtime.v1",
        "js/views/xblock", "js/views/modals/edit_xblock"],
($, _, gettext, XBlock, XBlockView, EditXBlockModal) ->
  class ModuleEdit extends XBlockView
    tagName: 'li'
    className: 'component'
    editorMode: 'editor-mode'

    events:
      "click .edit-button": 'clickEditButton'
      "click .delete-button": 'onDelete'

    initialize: ->
      @onDelete = @options.onDelete
      @render()

    loadDisplay: ->
      # Not all components render an inline student view, e.g. child containers which
      # instead render a link to a separate container page.
      xblockElement = @$el.find('.xblock-student_view')
      if xblockElement.length > 0
        XBlock.initializeBlock(xblockElement)

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
          cache: false
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
      modal = new EditXBlockModal();
      modal.edit(this.$el, self.model, { refresh: _.bind(@render, this) })
