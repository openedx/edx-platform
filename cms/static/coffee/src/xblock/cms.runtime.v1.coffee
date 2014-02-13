define ["jquery", "xblock/runtime.v1", "URI"], ($, XBlock, URI) ->
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
      handlerUrl: (element, handlerName, suffix, query, thirdparty) ->
        uri = URI("/xblock").segment($(element).data('usage-id'))
                                    .segment('handler')
                                    .segment(handlerName)
        if suffix? then uri.segment(suffix)
        if query? then uri.search(query)
        uri.toString()
