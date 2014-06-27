define ["jquery", "jquery.ui", "gettext", "backbone",
        "js/views/feedback_notification", "js/views/feedback_prompt",
        "coffee/src/views/module_edit", "js/models/module_info",
        "js/views/baseview", "js/views/components/add_xblock"],
($, ui, gettext, Backbone, NotificationView, PromptView, ModuleEditView, ModuleModel, BaseView, AddXBlockComponent) ->
    class UnitEditView extends BaseView
        events:
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

            @addXBlockComponent = new AddXBlockComponent(
                collection: @options.templates
                el: @$('.add-xblock-component')
                createComponent: (template) =>
                    return @createComponent(template, "Creating new component").done(
                        (editor) ->
                            listPanel = @$newComponentItem.prev()
                            listPanel.append(editor.$el)
                    ))
            @addXBlockComponent.render()

            @model.on('change:state', @render)

            @$newComponentItem = @$('.new-component-item')

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

        createComponent: (data, analytics_message) =>
            self = this
            operation = $.Deferred()
            editor = new ModuleEditView(
                onDelete: @deleteComponent
                model: new ModuleModel()
            )

            callback = ->
                operation.resolveWith(self, [editor])
                analytics.track analytics_message,
                    course: course_location_analytics
                    unit_id: unit_location_analytics
                    type: editor.$el.data('locator')

            editor.createItem(
                @$el.data('locator'),
                data,
                callback
            )

            return operation.promise()

        duplicateComponent: (event) =>
            self = this
            event.preventDefault()
            $component = $(event.currentTarget).parents('.component')
            source_locator = $component.data('locator')
            @runOperationShowingMessage(gettext('Duplicating&hellip;'), ->
                operation = self.createComponent(
                    {duplicate_source_locator: source_locator},
                    "Duplicating " + source_locator);
                operation.done(
                    (editor) ->
                        originalOffset = @getScrollOffset($component)
                        $component.after(editor.$el)
                        # Scroll the window so that the new component replaces the old one
                        @setScrollOffset(editor.$el, originalOffset)
                ))

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
            self = this
            event.preventDefault()
            @confirmThenRunOperation(gettext('Delete this component?'),
                gettext('Deleting this component is permanent and cannot be undone.'),
                gettext('Yes, delete this component'),
            ->
                self.runOperationShowingMessage(gettext('Deleting&hellip;'),
                ->
                    $component = $(event.currentTarget).parents('.component')
                    return $.ajax({
                        type: 'DELETE',
                        url: self.model.urlRoot + "/" + $component.data('locator')
                    }).success(=>
                        analytics.track "Deleted a Component",
                            course: course_location_analytics
                            unit_id: unit_location_analytics
                            id: $component.data('locator')

                        $component.remove()
                        # b/c we don't vigilantly keep children up to date
                        # get rid of it before it hurts someone
                        self.model.save({children: self.components()},
                            {
                                success: (model) ->
                                    model.unset('children')
                            })
                    )))

        deleteDraft: (event) ->
            @wait(true)
            $.ajax({
                type: 'DELETE',
                url: @model.url()
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

                @model.set('state', @$('.visibility-select').val()))

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
