class StudentNotes
    _debug: false

    targets: [] # holds elements with annotator() instances

    # Adds a listener for "notes" events that may bubble up from descendants.
    constructor: ($, el) ->
        console.log 'student notes init', arguments, this if @_debug

        if not $(el).data('notes-instance')
            events = 'notes:init': @onInitNotes
            $(el).delegate('*', events)
            $(el).data('notes-instance', @)

    # Initializes annotations on a container element in response to an init event.
    onInitNotes: (event, uri=null) =>
        event.stopPropagation()

        storeConfig = @getStoreConfig uri
        found = @targets.some (target) -> target is event.target

        if found
            annotator = $(event.target).data('annotator')
            if annotator
                store = annotator.plugins['Store']
                $.extend(store.options, storeConfig)
                if uri
                    store.loadAnnotationsFromSearch(storeConfig['loadFromSearch'])
                else
                    console.log 'URI is required to load annotations'
            else
                console.log 'No annotator() instance found for target: ', event.target
        else
            $(event.target).annotator()
                .annotator('addPlugin', 'Tags')
                .annotator('addPlugin', 'Store', storeConfig)
            @targets.push(event.target)

    # Returns a JSON config object that can be passed to the annotator Store plugin
    getStoreConfig: (uri) ->
        prefix = @getPrefix()
        if uri is null
            uri = @getURIPath()

        storeConfig =
            prefix: prefix
            loadFromSearch:
                uri: uri
                limit: 0
            annotationData:
                uri: uri
        storeConfig

    # Returns the API endpoint for the annotation store
    getPrefix: () ->
        re = /^(\/courses\/[^/]+\/[^/]+\/[^/]+)/
        match = re.exec(@getURIPath())
        prefix = (if match then match[1] else '')
        return "#{prefix}/notes/api"

    # Returns the URI path of the current page for filtering annotations
    getURIPath: () ->
        window.location.href.toString().split(window.location.host)[1]


# Enable notes by default on the document root.
# To initialize annotations on a container element in the document:
#
#   $('#myElement').trigger('notes:init');
#
# Comment this line to disable notes.

$(document).ready ($) -> new StudentNotes $, @
