class CMS.Views.CapaWikiEdit extends Backbone.View
  tagName: 'section'
  className: 'edit-pane'

  events:
    'click .cancel': 'cancel'
    'click .module-edit': 'editSubmodule'
    'click .save-update': 'save'
    'keyup .capa-box': 'checkAutoSave'
    'keyup .wiki-box': 'runParser'
    'change .wiki-box': 'runParser'

  initialize: ->
    @$el.load @model.editUrl(), =>
      @descriptor = XModule.loadModule($(@el).find('.xmodule_edit'))
      @capa_box = $(".capa-box", @el)
      @wiki_box = $(".wiki-box", @el)
      @message_box = $(".message-box", @el)
      @model.module = @descriptor
      @throttledAutoSave = _.throttle(@autoSave, 0);
      XModule.loadModules('display')

  debug: (msg) ->
    # console.log msg

  checkAutoSaveTimeout: ->
    @auto_save_timer = null
    @throttledAutoSave()

  checkAutoSave: =>
    callback = _.bind(@checkAutoSaveTimeout, this)
    if @auto_save_timer
      @auto_save_timer = window.clearTimeout(@auto_save_timer)
    @auto_save_timer = window.setTimeout(callback, 1000)

  hideMessage: ->
    @message_box.text ""

  showMessage: (message) ->
    @message_box.text message

  showError: (message) ->
    @showMessage(message)

  runParser: ->
    out = @descriptor.parse @wiki_box.val()
    if out.status == "success"
      out = @descriptor.convert out.result
      if out.status == "success"
        @capa_box.val out.xml
        @checkAutoSave()
        @hideMessage()
    @showMessage(out.message)

  autoSave: ->
    @model.save().done((previews) =>
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
    if moduleType == "CapaWikiDescriptor"
      CMS.pushView new CMS.Views.CapaWikiEdit
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
