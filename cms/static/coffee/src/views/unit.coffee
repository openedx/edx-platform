class CMS.Views.UnitEdit extends Backbone.View
  events:
    'click .new-component .new-component-type a.multiple-templates': 'showComponentTemplates'
    'click .new-component .new-component-type a.single-template': 'saveNewComponent'
    'click .new-component .cancel-button': 'closeNewComponent'
    'click .new-component-templates .new-component-template a': 'saveNewComponent'
    'click .new-component-templates .cancel-button': 'closeNewComponent'
    'click .delete-draft': 'deleteDraft'
    'click .create-draft': 'createDraft'
    'click .publish-draft': 'publishDraft'
    'change .visibility-select': 'setVisibility'

  initialize: =>
    @visibilityView = new CMS.Views.UnitEdit.Visibility(
      el: @$('.visibility-select')
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
      update: (event, ui) =>
        analytics.track "Reordered Components",
          course: course_location_analytics
          id: unit_location_analytics

        payload = children : @components()
        options = success : => @model.unset('children')
        @model.save(payload, options)
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

  showComponentTemplates: (event) =>
    event.preventDefault()

    type = $(event.currentTarget).data('type')
    @$newComponentTypePicker.slideUp(250)
    @$(".new-component-#{type}").slideDown(250)
    $('html, body').animate({
      scrollTop: @$(".new-component-#{type}").offset().top
    }, 500)

  closeNewComponent: (event) =>
    event.preventDefault()

    @$newComponentTypePicker.slideDown(250)
    @$newComponentTemplatePickers.slideUp(250)
    @$newComponentItem.removeClass('adding')
    @$newComponentItem.find('.rendered-component').remove()

  saveNewComponent: (event) =>
    event.preventDefault()

    editor = new CMS.Views.ModuleEdit(
      onDelete: @deleteComponent
      model: new CMS.Models.Module()
    )

    @$newComponentItem.before(editor.$el)

    editor.createItem(
      @$el.data('id'),
      $(event.currentTarget).data()
    )

    analytics.track "Added a Component",
      course: course_location_analytics
      unit_id: unit_location_analytics
      type: $(event.currentTarget).data('location')

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
    msg = new CMS.Views.Prompt.Warning(
      title: gettext('Delete this component?'),
      message: gettext('Deleting this component is permanent and cannot be undone.'),
      actions:
        primary:
          text: gettext('Yes, delete this component'),
          click: (view) =>
            view.hide()
            deleting = new CMS.Views.Notification.Mini
              title: gettext('Deleting') + '&hellip;',
            deleting.show()
            $component = $(event.currentTarget).parents('.component')
            $.post('/delete_item', {
              id: $component.data('id')
            }, =>
              deleting.hide()
              analytics.track "Deleted a Component",
                course: course_location_analytics
                unit_id: unit_location_analytics
                id: $component.data('id')

              $component.remove()
              # b/c we don't vigilantly keep children up to date
              # get rid of it before it hurts someone
              # sorry for the js, i couldn't figure out the coffee equivalent
              `_this.model.save({children: _this.components()},
                {success: function(model) {
                model.unset('children');
                }}
              );`
            )
        secondary:
          text: gettext('Cancel'),
          click: (view) ->
            view.hide()
    )
    msg.show()

  deleteDraft: (event) ->
    @wait(true)

    $.post('/delete_item', {
      id: @$el.data('id')
      delete_children: true
    }, =>
      analytics.track "Deleted Draft",
        course: course_location_analytics
        unit_id: unit_location_analytics

      window.location.reload()
    )

  createDraft: (event) ->
    @wait(true)

    $.post('/create_draft', {
      id: @$el.data('id')
    }, =>
      analytics.track "Created Draft",
        course: course_location_analytics
        unit_id: unit_location_analytics

      @model.set('state', 'draft')
    )

  publishDraft: (event) ->
    @wait(true)
    @saveDraft()

    $.post('/publish_draft', {
      id: @$el.data('id')
    }, =>
      analytics.track "Published Draft",
        course: course_location_analytics
        unit_id: unit_location_analytics

      @model.set('state', 'public')
    )

  setVisibility: (event) ->
    if @$('.visibility-select').val() == 'private'
      target_url = '/unpublish_unit'
      visibility = "private"
    else
      target_url = '/publish_draft'
      visibility = "public"

    @wait(true)

    $.post(target_url, {
      id: @$el.data('id')
    }, =>
      analytics.track "Set Unit Visibility",
        course: course_location_analytics
        unit_id: unit_location_analytics
        visibility: visibility

      @model.set('state', @$('.visibility-select').val())
    )

class CMS.Views.UnitEdit.NameEdit extends Backbone.View
  events:
    'change .unit-display-name-input': 'saveName'

  initialize: =>
    @model.on('change:metadata', @render)
    @model.on('change:state', @setEnabled)
    @setEnabled()
    @saveName
    @$spinner = $('<span class="spinner-in-field-icon"></span>');

  render: =>
    @$('.unit-display-name-input').val(@model.get('metadata').display_name)

  setEnabled: =>
    disabled = @model.get('state') == 'public'
    if disabled
      @$('.unit-display-name-input').attr('disabled', true)
    else
      @$('.unit-display-name-input').removeAttr('disabled')

  saveName: =>
    # Treat the metadata dictionary as immutable
    metadata = $.extend({}, @model.get('metadata'))
    metadata.display_name = @$('.unit-display-name-input').val()
    @model.save(metadata: metadata)
    # Update name shown in the right-hand side location summary.
    $('.unit-location .editing .unit-name').html(metadata.display_name)
    analytics.track "Edited Unit Name",
      course: course_location_analytics
      unit_id: unit_location_analytics
      display_name: metadata.display_name


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
