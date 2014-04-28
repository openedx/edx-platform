define ["jquery", "jquery.ui", "gettext", "backbone",
        "js/views/feedback_notification", "js/views/feedback_prompt",
        "coffee/src/views/module_edit", "js/models/module_info",
        "js/views/baseview"],
($, ui, gettext, Backbone, NotificationView, PromptView, ModuleEditView, ModuleModel, BaseView) ->
    class UnitEditView extends BaseView
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
            "click .component-actions .duplicate-button": 'duplicateComponent'

        initialize: =>
            @visibilityView = new UnitEditView.Visibility(
                el: @$('.visibility-select')
                model: @model
            )

            @locationView = new UnitEditView.LocationState(
                el: @$('.section-item.editing a')
                model: @model
            )

            @nameView = new UnitEditView.NameEdit(
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
                    saving = new NotificationView.Mini
                        title: gettext('Saving&hellip;')
                    saving.show()
                    options = success : =>
                        @model.unset('children')
                        saving.hide()
                    @model.save(payload, options)
                helper: 'clone'
                opacity: '0.5'
                placeholder: 'component-placeholder'
                forcePlaceholderSize: true
                axis: 'y'
                items: '> .component'
            )

            @$('.component').each (idx, element) =>
                model = new ModuleModel
                    id: $(element).data('locator')
                new ModuleEditView
                    el: element,
                    onDelete: @deleteComponent,
                    model: model

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

        createComponent: (event, data, notification_message, analytics_message, success_callback) =>
            event.preventDefault()

            editor = new ModuleEditView(
                onDelete: @deleteComponent
                model: new ModuleModel()
            )

            notification = new NotificationView.Mini
                title: notification_message

            notification.show()

            callback = ->
                notification.hide()
                success_callback()
                analytics.track analytics_message,
                    course: course_location_analytics
                    unit_id: unit_location_analytics
                    type: editor.$el.data('locator')

            editor.createItem(
                @$el.data('locator'),
                data,
                callback
            )

            return editor

        saveNewComponent: (event) =>
            success_callback = =>
                @$newComponentItem.before(editor.$el)
            editor = @createComponent(
                event, $(event.currentTarget).data(),
                gettext('Adding&hellip;'),
                "Creating new component",
                success_callback
            )
            @closeNewComponent(event)

        duplicateComponent: (event) =>
            $component = $(event.currentTarget).parents('.component')
            source_locator = $component.data('locator')
            success_callback = ->
                $component.after(editor.$el)
                $('html, body').animate({
                    scrollTop: editor.$el.offset().top
                }, 500)
            editor = @createComponent(
                event,
                {duplicate_source_locator: source_locator},
                gettext('Duplicating&hellip;')
                "Duplicating " + source_locator,
                success_callback
            )

        components: => @$('.component').map((idx, el) -> $(el).data('locator')).get()

        wait: (value) =>
            @$('.unit-body').toggleClass("waiting", value)

        render: =>
            if @model.hasChanged('state')
                @$el.toggleClass("edit-state-#{@model.previous('state')} edit-state-#{@model.get('state')}")
                @wait(false)

        saveDraft: =>
            @model.save()

        deleteComponent: (event) =>
            event.preventDefault()
            msg = new PromptView.Warning(
                title: gettext('Delete this component?'),
                message: gettext('Deleting this component is permanent and cannot be undone.'),
                actions:
                    primary:
                        text: gettext('Yes, delete this component'),
                        click: (view) =>
                            view.hide()
                            deleting = new NotificationView.Mini
                                title: gettext('Deleting&hellip;'),
                            deleting.show()
                            $component = $(event.currentTarget).parents('.component')
                            $.ajax({
                                type: 'DELETE',
                                url: @model.urlRoot + "/" + $component.data('locator')
                            }).success(=>
                                deleting.hide()
                                analytics.track "Deleted a Component",
                                    course: course_location_analytics
                                    unit_id: unit_location_analytics
                                    id: $component.data('locator')

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
            $.ajax({
                type: 'DELETE',
                url: @model.url() + "?" + $.param({recurse: true})
            }).success(=>

                analytics.track "Deleted Draft",
                    course: course_location_analytics
                    unit_id: unit_location_analytics

                window.location.reload()
            )

        createDraft: (event) ->
            self = this
            @disableElementWhileRunning($(event.target), ->
                self.wait(true)

                $.postJSON(self.model.url(), {
                        publish: 'create_draft'
                    }, =>
                    analytics.track "Created Draft",
                        course: course_location_analytics
                        unit_id: unit_location_analytics

                    self.model.set('state', 'draft')
                )
            )

        publishDraft: (event) ->
            self = this
            @disableElementWhileRunning($(event.target), ->
                self.wait(true)
                self.saveDraft()

                $.postJSON(self.model.url(), {
                        publish: 'make_public'
                    }, =>
                    analytics.track "Published Draft",
                        course: course_location_analytics
                        unit_id: unit_location_analytics

                    self.model.set('state', 'public')
                )
            )

        setVisibility: (event) ->
            if @$('.visibility-select').val() == 'private'
                action = 'make_private'
                visibility = "private"
            else
                action = 'make_public'
                visibility = "public"

            @wait(true)

            $.postJSON(@model.url(), {
                    publish: action
                }, =>
                analytics.track "Set Unit Visibility",
                    course: course_location_analytics
                    unit_id: unit_location_analytics
                    visibility: visibility

                @model.set('state', @$('.visibility-select').val())
            )

    class UnitEditView.NameEdit extends BaseView
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


    class UnitEditView.LocationState extends BaseView
        initialize: =>
            @model.on('change:state', @render)

        render: =>
            @$el.toggleClass("#{@model.previous('state')}-item #{@model.get('state')}-item")

    class UnitEditView.Visibility extends BaseView
        initialize: =>
            @model.on('change:state', @render)
            @render()

        render: =>
            @$el.val(@model.get('state'))

    return UnitEditView
