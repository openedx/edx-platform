class CMS.Views.UnitEdit extends Backbone.View
  events:
    'click .new-component .new-component-type a': 'showComponentTemplates'
    'click .new-component .cancel-button': 'closeNewComponent'
    'click .new-component-templates .new-component-template a': 'saveNewComponent'
    'click .new-component-templates .cancel-button': 'closeNewComponent'
    'click .new-component-button': 'showNewComponentForm'
    'click #save-draft': 'saveDraft'
    'click #delete-draft': 'deleteDraft'
    'click #create-draft': 'createDraft'
    'click #publish-draft': 'publishDraft'
    'change #visibility': 'setVisibility'

  initialize: =>
    @visibilityView = new CMS.Views.UnitEdit.Visibility(
      el: @$('#visibility')
      model: @model
    )

    @saveView = new CMS.Views.UnitEdit.SaveDraftButton(
      el: @$('#save-draft')
      model: @model
    )

    @locationView = new CMS.Views.UnitEdit.LocationState(
      el: @$('.section-item.editing a')
      model: @model
    )

    @nameView = new CMS.Views.UnitEdit.NameEdit(
      el: @$('.unit-name-input')
      model: @model
    )

    @model.on('change:state', @render)

    @$newComponentItem = @$('.new-component-item')
    @$newComponentTypePicker = @$('.new-component')
    @$newComponentTemplatePickers = @$('.new-component-templates')
    @$newComponentButton = @$('.new-component-button')

    @$('.components').sortable(
      handle: '.drag-handle'
      update: (event, ui) => @model.set('children', @components())
      helper: 'clone'
      opacity: '0.5'
      placeholder: 'component-placeholder'
      forcePlaceholderSize: true
      axis: 'y'
      items: '> .component'
    )

    @$('.component').each((idx, element) =>
        new CMS.Views.ModuleEdit(
            el: element,
            onDelete: @deleteComponent,
            model: new CMS.Models.Module(
                id: $(element).data('id'),
            )
        )
        update: (event, ui) => @model.set('children', @components())
    )

  # New component creation
  showNewComponentForm: (event) =>
    event.preventDefault()
    @$newComponentItem.addClass('adding')
    $(event.target).slideUp(150)
    @$newComponentTypePicker.slideDown(250)

  showComponentTemplates: (event) =>
    event.preventDefault()

    type = $(event.currentTarget).data('type')
    @$newComponentTypePicker.slideUp(250)
    @$(".new-component-#{type}").slideDown(250)

  closeNewComponent: (event) =>
    event.preventDefault()

    @$newComponentTypePicker.slideUp(250)
    @$newComponentTemplatePickers.slideUp(250)
    @$newComponentButton.slideDown(250)
    @$newComponentItem.removeClass('adding')
    @$newComponentItem.find('.rendered-component').remove()

  saveNewComponent: (event) =>
    event.preventDefault()

    editor = new CMS.Views.ModuleEdit(
      onDelete: @deleteComponent
      model: new CMS.Models.Module()
    )

    @$newComponentItem.before(editor.$el)

    editor.cloneTemplate(
      @$el.data('id'),
      $(event.currentTarget).data('location')
    )

    @closeNewComponent(event)

  components: => @$('.component').map((idx, el) -> $(el).data('id')).get()

  wait: (value) =>
    @$('.unit-body').toggleClass("waiting", value)

  render: =>
    if @model.hasChanged('state')
      @$el.toggleClass("edit-state-#{@model.previous('state')} edit-state-#{@model.get('state')}")
      @wait(false)

  saveDraft: =>
    @model.save()

  deleteComponent: (event) =>
    $component = $(event.currentTarget).parents('.component')
    $.post('/delete_item', {
      id: $component.data('id')
    }, =>
      $component.remove()
      @saveOrder()
    )

  deleteDraft: (event) ->
    @wait(true)

    $.post('/delete_item', {
      id: @$el.data('id')
      delete_children: true
    }, =>
      window.location.reload()
    )

  createDraft: (event) ->
    @wait(true)

    $.post('/create_draft', {
      id: @$el.data('id')
    }, =>
      @model.set('state', 'draft')
    )

  publishDraft: (event) ->
    @wait(true)
    @saveDraft()

    $.post('/publish_draft', {
      id: @$el.data('id')
    }, =>
      @model.set('state', 'public')
    )

  setVisibility: (event) ->
    if @$('#visibility').val() == 'private'
      target_url = '/unpublish_unit'
    else
      target_url = '/publish_draft'

    @wait(true)

    $.post(target_url, {
      id: @$el.data('id')
    }, =>
      @model.set('state', @$('#visibility').val())
    )

class CMS.Views.UnitEdit.NameEdit extends Backbone.View
  events:
    "keyup .unit-display-name-input": "saveName"

  initialize: =>
    @model.on('change:metadata', @render)
    @saveName

  render: =>
    @$('.unit-display-name-input').val(@model.get('metadata').display_name)

  saveName: =>
    # Treat the metadata dictionary as immutable
    metadata = $.extend({}, @model.get('metadata'))
    metadata.display_name = @$('.unit-display-name-input').val()
    @model.set('metadata', metadata)

class CMS.Views.UnitEdit.LocationState extends Backbone.View
  initialize: =>
    @model.on('change:state', @render)
  
  render: =>
    @$el.toggleClass("#{@model.previous('state')}-item #{@model.get('state')}-item")

class CMS.Views.UnitEdit.Visibility extends Backbone.View
  initialize: =>
    @model.on('change:state', @render)
    @render()

  render: =>
    @$el.val(@model.get('state'))

class CMS.Views.UnitEdit.SaveDraftButton extends Backbone.View
  initialize: =>
    @model.on('change:children', @enable)
    @model.on('change:metadata', @enable)
    @model.on('sync', @disable)

    @disable()
  
  disable: =>
    @$el.addClass('disabled')

  enable: =>
    @$el.removeClass('disabled')