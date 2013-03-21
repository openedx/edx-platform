class @StudentNotes
    targets: []

    storeConfig:
        prefix: ''
        annotationData:
            uri: ''

    constructor: () ->
        @storeConfig =
            prefix: @getPrefix()
            annotationData:
                uri: @getURIPath()

        $(document).ready(@init)

    init: ($) =>
        if not StudentNotes.ready
            $(document).delegate('*', {
                'notes:init': @onInitNotes,
                'notes:load': @onLoadNotes
            })
            StudentNotes.ready = true

    onInitNotes: (event, annotationData=null) =>
        found = (target for target in @targets when target is event.target)

        storeConfig = $.extend {}, @storeConfig
        $.extend(storeConfig.annotationData, annotationData) if annotationData

        if found.length is 0
            $(event.target).annotator()
              .annotator('addPlugin', 'Tags')
              .annotator('addPlugin', 'Store', storeConfig)

            @targets.push(event.target)

    onLoadNotes: (event) =>
        if event.target in @targets
            $(event.target).annotator().annotator('loadAnnotations')

    getPrefix: () ->
        re = /^(\/courses\/[^/]+\/[^/]+\/[^/]+)/
        match = re.exec(@getURIPath())
        prefix = (if match then match[1] else '')
        return "#{prefix}/notes/api"

    getURIPath: () ->
        window.location.href.toString().split(window.location.host)[1]
