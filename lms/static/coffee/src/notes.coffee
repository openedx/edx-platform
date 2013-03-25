class StudentNotes
    _debug: true

    targets: [] # elements with annotator() instances

    constructor: ($, el) ->
        console.log 'student notes init', arguments, this if @_debug

        if $(el).data('notes-ready') isnt 'yes'
            $(el).delegate '*', 'notes:init': @onInitNotes
            $(el).data('notes-ready', 'yes')

    onInitNotes: (event, annotationData=null) =>
        event.stopPropagation()

        found = @targets.some (target) -> target is event.target

        if found
            annotator = $(event.target).data('annotator')
            store = annotator.plugins['Store']
            store.options.annotationData = annotationData if annotationData
            store.loadAnnotations()
        else
            $(event.target).annotator()
                .annotator('addPlugin', 'Tags')
                .annotator('addPlugin', 'Store', @getStoreConfig(annotationData))
            @targets.push(event.target)

    getStoreConfig: (annotationData) ->
        storeConfig =
            prefix: @getPrefix()
            annotationData:
                uri: @getURIPath() # defaults to current URI path

        $.extend storeConfig.annotationData, annotationData  if annotationData
        storeConfig

    getPrefix: () ->
        re = /^(\/courses\/[^/]+\/[^/]+\/[^/]+)/
        match = re.exec(@getURIPath())
        prefix = (if match then match[1] else '')
        return "#{prefix}/notes/api"

    getURIPath: () ->
        window.location.href.toString().split(window.location.host)[1]

$(document).ready ($) -> new StudentNotes($, this)