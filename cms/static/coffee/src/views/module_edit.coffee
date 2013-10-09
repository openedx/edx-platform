define ["backbone", "jquery", "underscore", "gettext", "xmodule",
        "js/views/feedback_notification", "js/views/metadata", "js/collections/metadata"
        "jquery.inputnumber"],
(Backbone, $, _, gettext, XModule, NotificationView, MetadataView, MetadataCollection) ->
  class ModuleEdit extends Backbone.View
    tagName: 'li'
    className: 'component'
    editorMode: 'editor-mode'

    events:
      "click .component-editor .cancel-button": 'clickCancelButton'
      "click .component-editor .save-button": 'clickSaveButton'
      "click .component-actions .edit-button": 'clickEditButton'
      "click .component-actions .delete-button": 'onDelete'
      "click .mode a": 'clickModeButton'

    initialize: ->
      @onDelete = @options.onDelete
      @render()

    $component_editor: => @$el.find('.component-editor')

    loadDisplay: ->
      XModule.loadModule(@$el.find('.xmodule_display'))

    loadEdit: ->
      if not @module
        @module = XModule.loadModule(@$el.find('.xmodule_edit'))
        # At this point, metadata-edit.html will be loaded, and the metadata (as JSON) is available.
        metadataEditor = @$el.find('.metadata_edit')
        metadataData = metadataEditor.data('metadata')
        models = [];
        for key of metadataData
          models.push(metadataData[key])
        @metadataEditor = new MetadataView.Editor({
            el: metadataEditor,
            collection: new MetadataCollection(models)
        })

        # Need to update set "active" class on data editor if there is one.
        # If we are only showing settings, hide the data editor controls and update settings accordingly.
        if @hasDataEditor()
          @selectMode(@editorMode)
        else
          @hideDataEditor()

        title = interpolate(gettext('<em>Editing:</em> %s'),
          [@metadataEditor.getDisplayName()])
        @$el.find('.component-name').html(title)

    customMetadata: ->
        # Hack to support metadata fields that aren't part of the metadata editor (ie, LaTeX high level source).
        # Walk through the set of elements which have the 'data-metadata_name' attribute and
        # build up an object to pass back to the server on the subsequent POST.
        # Note that these values will always be sent back on POST, even if they did not actually change.
        _metadata = {}
        _metadata[$(el).data("metadata-name")] = el.value for el in $('[data-metadata-name]',  @$component_editor())
        return _metadata

    changedMetadata: ->
      return _.extend(@metadataEditor.getModifiedMetadataValues(), @customMetadata())

    createItem: (parent, payload) ->
      payload.parent_location = parent
      $.post(
          "/create_item"
          payload
          (data) =>
              @model.set(id: data.id)
              @$el.data('id', data.id)
              @render()
      )

    render: ->
      if @model.id
        @$el.load("/preview_component/#{@model.id}", =>
          @loadDisplay()
          @delegateEvents()
        )

    clickSaveButton: (event) =>
      event.preventDefault()
      data = @module.save()

      analytics.track "Saved Module",
        course: course_location_analytics
        id: _this.model.id

      data.metadata = _.extend(data.metadata || {}, @changedMetadata())
      @hideModal()
      saving = new NotificationView.Mini
        title: gettext('Saving&hellip;')
      saving.show()
      @model.save(data).done( =>
      #   # showToastMessage("Your changes have been saved.", null, 3)
        @module = null
        @render()
        @$el.removeClass('editing')
        saving.hide()
      )

    clickCancelButton: (event) ->
      event.preventDefault()
      @$el.removeClass('editing')
      @$component_editor().slideUp(150)
      @hideModal()

    hideModal: ->
      $modalCover = $(".modal-cover")
      $modalCover.hide()
      $modalCover.removeClass('is-fixed')

    clickEditButton: (event) ->
      event.preventDefault()
      @$el.addClass('editing')
      $(".modal-cover").show().addClass('is-fixed')
      @$component_editor().slideDown(150)
      @loadEdit()

    clickModeButton: (event) ->
      event.preventDefault()
      if not @hasDataEditor()
        return
      @selectMode(event.currentTarget.parentElement.id)

    hasDataEditor: =>
      return @$el.find('.wrapper-comp-editor').length > 0

    selectMode: (mode) =>
      dataEditor = @$el.find('.wrapper-comp-editor')
      settingsEditor = @$el.find('.wrapper-comp-settings')
      editorModeButton =  @$el.find('#editor-mode').find("a")
      settingsModeButton = @$el.find('#settings-mode').find("a")

      if mode == @editorMode
        # Because of CodeMirror editor, cannot hide the data editor when it is first loaded. Therefore
        # we have to use a class of is-inactive instead of is-active.
        dataEditor.removeClass('is-inactive')
        editorModeButton.addClass('is-set')
        settingsEditor.removeClass('is-active')
        settingsModeButton.removeClass('is-set')
      else
        dataEditor.addClass('is-inactive')
        editorModeButton.removeClass('is-set')
        settingsEditor.addClass('is-active')
        settingsModeButton.addClass('is-set')

    hideDataEditor: =>
      editorModeButtonParent =  @$el.find('#editor-mode')
      editorModeButtonParent.addClass('inactive-mode')
      editorModeButtonParent.removeClass('active-mode')
      @$el.find('.wrapper-comp-settings').addClass('is-active')
      @$el.find('#settings-mode').find("a").addClass('is-set')
