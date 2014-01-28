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

        # Get uri   
        unless uri.substring(0, 4) is "http"
            uri_root = (window.location.href.split(/#|\?/).shift() or "")
            uri = uri_root + uri.substring(1)
        parts = window.location.href.split("/")
        courseid = parts[4] + "/" + parts[5] + "/" + parts[6]

        # Get id and name user    
        idUdiv = $(event.target).parent().find(".idU")[0]
        idDUdiv = $(event.target).parent().find(".idDU")[0]
        idUdiv = (if typeof idUdiv isnt "undefined" then idUdiv.innerHTML else "")
        idDUdiv = (if typeof idDUdiv isnt "undefined" then idDUdiv.innerHTML else "")
        
        options = 
            optionsAnnotator:
                permissions:
                    user:
                        id: idUdiv
                        name: idDUdiv

                    userString: (user) ->
                        return user.name  if user and user.name
                        user

                    userId: (user) ->
                        return user.id  if user and user.id
                        user 
                auth: 
                    tokenUrl: location.protocol+'//'+location.host+"/token?course_id="+courseid

                store:
                    prefix: 'http://catch.aws.af.cm/annotator'

                    annotationData: uri:uri

                    urls: 
                        create:  '/create',
                        read:    '/read/:id',
                        update:  '/update/:id',
                        destroy: '/delete/:id',
                        search:  '/search'

                    loadFromSearch:
                        limit:10000
                        uri: uri
                        user:idUdiv
					    
            optionsVideoJS: techOrder: ["html5","flash","youtube"],customControlsOnMobile: true
            optionsOVA: 
                posBigNew:'none'
                NumAnnotations:20
            optionsRichText: 
                tinymce:
                    selector: "li.annotator-item textarea"
                    plugins: "media image insertdatetime link code"
                    menubar: false
                    toolbar_items_size: 'small'
                    extended_valid_elements : "iframe[src|frameborder|style|scrolling|class|width|height|name|align|id]"
                    toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image media rubric | code "
                    
        if found
            $(event.target).annotator "destroy"  unless Annotator._instances.length is 0
            ova = new OpenVideoAnnotation.Annotator($(event.target), options)
        else
            if event.target.id is "annotator-viewer"
                ova = new OpenVideoAnnotation.Annotator($(event.target), options)  
            else
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
