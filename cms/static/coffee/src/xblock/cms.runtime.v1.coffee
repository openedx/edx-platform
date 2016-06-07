define [
    "jquery", "backbone", "xblock/runtime.v1", "URI", "gettext",
    "js/utils/modal", "common/js/components/views/feedback_notification"
], ($, Backbone, XBlock, URI, gettext, ModalUtils, NotificationView) ->

    @BaseRuntime = {}

    class BaseRuntime.v1 extends XBlock.Runtime.v1
        handlerUrl: (element, handlerName, suffix, query, thirdparty) ->
            uri = URI(@handlerPrefix).segment($(element).data('usage-id'))
            .segment('handler')
            .segment(handlerName)
            if suffix? then uri.segment(suffix)
            if query? then uri.search(query)
            uri.toString()

        constructor: () ->
            super()
            @dispatcher = _.clone(Backbone.Events)
            @listenTo('save', @_handleSave)
            @listenTo('cancel', @_handleCancel)
            @listenTo('error', @_handleError)
            @listenTo('modal-shown', (data) ->
                @modal = data)
            @listenTo('modal-hidden', () ->
                @modal = null)
            @listenTo('page-shown', (data) ->
                @page = data)

        # Notify the Studio client-side runtime of an event so that it can update the UI in a consistent way.
        notify: (name, data) ->
            @dispatcher.trigger(name, data)

        # Listen to a Studio event and invoke the specified callback when it is triggered.
        listenTo: (name, callback) ->
            @dispatcher.bind(name, callback, this)

        # Refresh the view for the xblock represented by the specified element.
        refreshXBlock: (element) ->
            if @page
                @page.refreshXBlock(element)

        _handleError: (data) ->
            message = data.message || data.msg
            if message
                # TODO: remove 'Open Assessment' specific default title
                title = data.title || gettext("OpenAssessment Save Error")
                @alert = new NotificationView.Error
                    title: title
                    message: message
                    closeIcon: false
                    shown: false
                @alert.show()

        _handleSave: (data) ->
            # Starting to save, so show a notification
            if data.state == 'start'
                message = data.message || gettext('Saving')
                @notification = new NotificationView.Mini
                    title: message
                @notification.show()

            # Finished saving, so hide the notification and refresh appropriately
            else if data.state == 'end'
                @_hideAlerts()

                # Notify the modal that the save has completed so that it can hide itself
                # and then refresh the xblock.
                if @modal and @modal.onSave
                    @modal.onSave()
                # ... else ask it to refresh the newly saved xblock
                else if data.element
                    @refreshXBlock(data.element)

                @notification.hide()

        _handleCancel: () ->
            @_hideAlerts()
            if @modal
                @modal.cancel()
                @notify('modal-hidden')

        _hideAlerts: () ->
            # Hide any alerts that are being shown
            if @alert && @alert.options.shown
                @alert.hide()

    @PreviewRuntime = {}

    class PreviewRuntime.v1 extends BaseRuntime.v1
        handlerPrefix: '/preview/xblock'

    @StudioRuntime = {}

    class StudioRuntime.v1 extends BaseRuntime.v1
        handlerPrefix: '/xblock'
