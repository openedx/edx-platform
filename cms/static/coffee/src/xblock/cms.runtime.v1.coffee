define [
    "jquery", "xblock/runtime.v1", "URI", "gettext",
    "js/utils/modal", "js/views/feedback_notification"
], ($, XBlock, URI, gettext, ModalUtils, NotificationView) ->
    @PreviewRuntime = {}

    class PreviewRuntime.v1 extends XBlock.Runtime.v1
        handlerUrl: (element, handlerName, suffix, query, thirdparty) ->
            uri = URI("/preview/xblock").segment($(element).data('usage-id'))
            .segment('handler')
            .segment(handlerName)
            if suffix? then uri.segment(suffix)
            if query? then uri.search(query)
            uri.toString()

    @StudioRuntime = {}

    class StudioRuntime.v1 extends XBlock.Runtime.v1
        constructor: () ->
            super()
            @savingNotification = new NotificationView.Mini
                title: gettext('Saving&hellip;')
            @alert = new NotificationView.Error
                title: "OpenAssessment Save Error",
                closeIcon: false,
                shown: false

        handlerUrl: (element, handlerName, suffix, query, thirdparty) ->
            uri = URI("/xblock").segment($(element).data('usage-id'))
            .segment('handler')
            .segment(handlerName)
            if suffix? then uri.segment(suffix)
            if query? then uri.search(query)
            uri.toString()

        # Notify the Studio client-side runtime so it can update
        # the UI in a consistent way.  Currently, this is used
        # for save / cancel when editing an XBlock.
        # Although native XBlocks should handle their own persistence,
        # Studio still needs to update the UI in a consistent way
        # (showing the "Saving..." notification, closing the modal editing dialog, etc.)
        notify: (name, data) ->
            if name == 'save'
                if 'state' of data

                    # Starting to save, so show the "Saving..." notification
                    if data.state == 'start'
                        @savingNotification.show()

                        # Finished saving, so hide the "Saving..." notification
                    else if data.state == 'end'
                        @_hideAlerts()

                        # Notify the modal that the save has completed so that it can hide itself
                        # and then refresh the xblock.
                        if @modal
                            @modal.onSave()

                        @savingNotification.hide()

            else if name == 'edit-modal-shown'
                @modal = data

            else if name == 'edit-modal-hidden'
                @modal = null

            else if name == 'cancel'
                @_hideAlerts()
                if @modal
                    @modal.cancel()

            else if name == 'error'
                if 'msg' of data
                    @alert.options.message = data.msg
                    @alert.show()

        _hideAlerts: () ->
            # Hide any alerts that are being shown
            if @alert.options.shown
                @alert.hide()
