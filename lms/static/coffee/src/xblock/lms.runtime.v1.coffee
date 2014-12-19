@LmsRuntime = {}

class LmsRuntime.v1 extends XBlock.Runtime.v1
  handlerUrl: (element, handlerName, suffix, query, thirdparty) ->
    courseId = $(element).data("course-id")
    usageId = $(element).data("usage-id")
    blockFamily = $(element).data("block-family")
    handlerAuth = if thirdparty then "handler_noauth" else "handler"

    uri = URI('/courses').segment(courseId)
                         .segment(blockFamily)
                         .segment(usageId)
                         .segment(handlerAuth)
                         .segment(handlerName)

    if suffix? then uri.segment(suffix)
    if query? then uri.search(query)

    uri.toString()
