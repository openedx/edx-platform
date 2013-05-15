class CMS.Views.ModuleEdit extends Backbone.View
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
      @metadataEditor = new CMS.Views.Metadata.Editor({
          el: metadataEditor,
          model: new CMS.Models.MetadataEditor(metadataEditor.data('metadata'))
          });
      # Need to update set "active" class on data editor if there is one.
      # If we are only showing settings, hide the data editor controls and update settings accordingly.
      if @hasDataEditor()
        @selectMode(@editorMode)
      else
        @hideDataEditor()
      @$el.find('.component-name').html('<em>Editing:</em> ' + @metadataEditor.getDisplayName())

  changedMetadata: ->
    return @metadataEditor.getModifiedMetadataValues()

  cloneTemplate: (parent, template) ->
    $.post("/clone_item", {
      parent_location: parent
      template: template
    }, (data) => 
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
    @model.save(data).done( =>
    #   # showToastMessage("Your changes have been saved.", null, 3)
      @module = null
      @render()
      @$el.removeClass('editing')
    ).fail( ->
      showToastMessage("There was an error saving your changes. Please try again.", null, 3)
    )

  clickCancelButton: (event) ->
    event.preventDefault()
    @$el.removeClass('editing')
    @$component_editor().slideUp(150)
    @hideModal()

  hideModal: ->
    $modalCover.hide()
    $modalCover.removeClass('is-fixed')

  clickEditButton: (event) ->
    event.preventDefault()
    @$el.addClass('editing')
    $modalCover.show().addClass('is-fixed')
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
      dataEditor.addClass('is-active')
      settingsEditor.removeClass('is-active')
      editorModeButton.addClass('is-set')
      settingsModeButton.removeClass('is-set')
    else
      dataEditor.removeClass('is-active')
      settingsEditor.addClass('is-active')
      editorModeButton.removeClass('is-set')
      settingsModeButton.addClass('is-set')

  hideDataEditor: =>
    editorModeButtonParent =  @$el.find('#editor-mode')
    # Can it be enough to just remove active-mode?
    editorModeButtonParent.addClass('inactive-mode')
    editorModeButtonParent.removeClass('active-mode')
    @$el.find('.wrapper-comp-settings').addClass('is-active')
    @$el.find('#settings-mode').find("a").addClass('is-set')