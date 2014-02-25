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
                @_hide_editor()
                @savingNotification.show()

            # Finished saving, so hide the "Saving..." notification
            else if data.state == 'end'
                $('.component.editing').removeClass('editing')
                @savingNotification.hide()

        else if name == 'cancel'
            @_hide_editor()

      _hide_editor: () ->
          # This will close all open component editors, which works
          # if we assume that <= 1 are open at a time.
          el = $('.component.editing')
          el.removeClass('editing')
          el.find('.component-editor').slideUp(150)
          ModalUtils.hideModalCover()
