class CMS.Views.CapawikiEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  events:
    'click .cancel': 'cancel'
    'click .module-edit': 'editSubmodule'
    'click .save-update': 'save'
    'keyup .wiki-box': 'checkAutoSave'

  initialize: ->
    @$el.load @model.editUrl(), =>
      @descriptor = XModule.loadModule($(@el).find('.xmodule_edit'))
      @capa_box = $(".capa-box", @el)
      @wiki_box = $(".wiki-box", @el)
      @model.module = @descriptor
      @throttledAutoSave = _.throttle(@autoSave, 0);
      XModule.loadModules('display')

  checkAutoSaveTimeout: ->
    @auto_save_timer = null
    @throttledAutoSave()

  checkAutoSave: =>
    callback = _.bind(@checkAutoSaveTimeout, this)
    if @auto_save_timer
      @auto_save_timer = window.clearTimeout(@auto_save_timer)
    @auto_save_timer = window.setTimeout(callback, 1000)

  hideMessage: ->
    @message_box.css {"display":"none"}

  showMessage: (message) ->
    @message_box.css {"display":"block"}
    @message_box.text message

  showError: (message) ->
    @showMessage(message)

  autoSave: ->
    @model.save().done((previews) =>
      @hideMessage()
      previews_section = @$el.find('.previews').empty()
      $.each(previews, (idx, preview) =>
        preview_wrapper = $('<section/>', class: 'preview').append preview
        previews_section.append preview_wrapper
      )
      XModule.loadModules('display')
    ).fail(->
      @showMessage("There was an error saving your changes. Please try again.")
    )

  save: (event) ->
    event.preventDefault()
    @model.save().done((previews) =>
      alert("Your changes have been saved.")
      previews_section = @$el.find('.previews').empty()
      $.each(previews, (idx, preview) =>
        preview_wrapper = $('<section/>', class: 'preview').append preview
        previews_section.append preview_wrapper
      )

      XModule.loadModules('display')
    ).fail(->
      alert("There was an error saving your changes. Please try again.")
    )

  cancel: (event) ->
    event.preventDefault()
    CMS.popView()

  editSubmodule: (event) ->
    event.preventDefault()
    previewType = $(event.target).data('preview-type')
    moduleType = $(event.target).data('type')
    if moduleType == "CapawikiDescriptor"
      CMS.pushView new CMS.Views.CapawikiEdit
          model: new CMS.Models.Module
              id: $(event.target).data('id')
              type: if moduleType == 'None' then null else moduleType
              previewType: if previewType == 'None' then null else previewType
    else
      CMS.pushView new CMS.Views.ModuleEdit
          model: new CMS.Models.Module
              id: $(event.target).data('id')
              type: if moduleType == 'None' then null else moduleType
              previewType: if previewType == 'None' then null else previewType
