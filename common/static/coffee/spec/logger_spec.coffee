describe 'Logger', ->
    it 'expose window.log_event', ->
        expect(window.log_event).toBe Logger.log

    describe 'log', ->
        it 'send a request to log event', ->
            spyOn jQuery, 'postWithPrefix'
            Logger.log 'example', 'data'
            expect(jQuery.postWithPrefix).toHaveBeenCalledWith '/event',
                event_type: 'example'
                event: '"data"'
                page: window.location.href

    # Broken with commit 9f75e64? Skipping for now.
    xdescribe 'bind', ->
        beforeEach ->
            Logger.bind()
            Courseware.prefix = '/6002x'

        afterEach ->
            window.onunload = null

        it 'bind the onunload event', ->
            expect(window.onunload).toEqual jasmine.any(Function)

        it 'send a request to log event', ->
            spyOn($, 'ajax')
            window.onunload()
            expect($.ajax).toHaveBeenCalledWith
                url: "#{Courseware.prefix}/event",
                data:
                    event_type: 'page_close'
                    event: ''
                    page: window.location.href
                async: false
