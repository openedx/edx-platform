class CMS.Views.UnitEdit extends Backbone.View
  events:
    'click .new-component .new-component-type a': 'showComponentTemplates'
    'click .new-component .cancel-button': 'closeNewComponent'
    'click .new-component-templates .new-component-template a': 'saveNewComponent'
    'click .new-component-templates .cancel-button': 'closeNewComponent'
    'click .new-component-button': 'showNewComponentForm'
    'click .delete-draft': 'deleteDraft'
    'click .create-draft': 'createDraft'
    'click .publish-draft': 'publishDraft'
    'change .visibility-select': 'setVisibility'

  initialize: =>
    @visibilityView = new CMS.Views.UnitEdit.Visibility(
      el: @$('#visibility')
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
      update: (event, ui) => @model.save(children: @components())
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
    )

  # New component creation
  showNewComponentForm: (event) =>
    event.preventDefault()
    @$newComponentItem.addClass('adding')
    $(event.target).fadeOut(150)
    @$newComponentItem.css('height', @$newComponentTypePicker.outerHeight())
    @$newComponentTypePicker.slideDown(250)

  showComponentTemplates: (event) =>
    event.preventDefault()

    type = $(event.currentTarget).data('type')
    @$newComponentTypePicker.fadeOut(250)
    @$(".new-component-#{type}").fadeIn(250)

  closeNewComponent: (event) =>
    event.preventDefault()

    @$newComponentTypePicker.slideUp(250)
    @$newComponentTemplatePickers.slideUp(250)
    @$newComponentButton.fadeIn(250)
    @$newComponentItem.removeClass('adding')
    @$newComponentItem.find('.rendered-component').remove()
    @$newComponentItem.css('height', @$newComponentButton.outerHeight())

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
    if not confirm 'Are you sure you want to delete this component? This action cannot be undone.'
      return
    $component = $(event.currentTarget).parents('.component')
    $.post('/delete_item', {
      id: $component.data('id')
    }, =>
      $component.remove()
      @model.save(children: @components())
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
      @model.set('state', @$('.visibility-select').val())
    )

class CMS.Views.UnitEdit.NameEdit extends Backbone.View
  events:
    "keyup .unit-display-name-input": "saveName"

  initialize: =>
    @model.on('change:metadata', @render)
    @saveName
    @$spinner = $('<span class="spinner-in-field-icon"></span>');

  render: =>
    @$('.unit-display-name-input').val(@model.get('metadata').display_name)

  saveName: =>
    # Treat the metadata dictionary as immutable
    metadata = $.extend({}, @model.get('metadata'))
    metadata.display_name = @$('.unit-display-name-input').val()
    $('.unit-location .editing .unit-name').html(metadata.display_name)

    inputField = this.$el.find('input')

    # add a spinner
    @$spinner.css({
        'position': 'absolute',
        'top': Math.floor(inputField.position().top + (inputField.outerHeight() / 2) + 3),
        'left': inputField.position().left + inputField.outerWidth() - 24,
        'margin-top': '-10px'
    });
    inputField.after(@$spinner);

    # save the name after a slight delay
    if @timer
      clearTimeout @timer
    @timer = setTimeout( =>
      @model.save(metadata: metadata)
      @timer = null
      @$spinner.delay(500).fadeOut(150)
    , 500)

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
