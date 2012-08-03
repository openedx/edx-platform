class @CapaDescriptor
    constructor: (@element) ->
        @problem_text = ""
        @edit_box = $(".edit-box.capa-box", @element)
        @source_box = $(".edit-box.source-box", @element)
        @message_box = $(".parser-message-box", @element)
        @buildParser()
        @throttledAutoSave = _.throttle(@autoSave, 0);
        @source_box.keyup =>
            @parse()

    save: -> @edit_box.val()

    buildParser: ->
        $.get "/static/grammars/main.jspeg", (data) =>
            @grammar = data
            @parser = PEG.buildParser @grammar
        , "text"

    buildErrorMessage: (e) ->
        if e.line != undefined && e.column != undefined
            "Line " + e.line + ", column " + e.column + ": " + e.message
        else e.message

    checkAutoSaveTimeout: ->
        @auto_save_timer = null
        @throttledAutoSave()

    checkAutoSave: ->
        callback = _.bind(@checkAutoSaveTimeout, this)
        if @auto_save_timer
            @auto_save_timer = window.clearTimeout(@auto_save_timer)
        @auto_save_timer = window.setTimeout(callback, 1000)

    autoSave: (event) ->
        $(".silent-save-update").click();

    parse: ->
        try
            source = @source_box.val() + "\n"
            result = @parser.parse (source)
            console.log result
            @outputXML(result)
            @message_box.css {"display":"none"}
        catch e 
            console.log @buildErrorMessage(e)
            @message_box.html @buildErrorMessage(e)
            @message_box.css {"display":"block"}

    outputXML: (parsed) ->
        @edit_box.val @buildXML(parsed)
        @checkAutoSave()

    dom2capa: (node) ->
        serializer = new XMLSerializer()
        capa = serializer.serializeToString(node)

    buildXML: (parsed) ->
        dom_parser = new DOMParser()
        doc = dom_parser.parseFromString("<problem />", "text/xml");
        problem = $(doc).find('problem')

        create_text_element = (content) ->
            el = $(doc.createElement('text'))
            for line in content.split('\n')
                el.append doc.createTextNode(line)
                el.append doc.createElement('br')
            el.children().last().remove()
            return el

        variable_name_wrapper = (expression) ->
            match = /^\{(.+)\}$/.exec(expression)
            return if match then "$" + match[1] else expression

        for section in parsed
            if section.type == 'text'
                newel = create_text_element(section.text)
                problem.append(newel)

            else if section.type == 'image'
                center = $(doc.createElement('center'))
                img = $(doc.createElement('img'))
                img.attr 'src', section.url
                center.append img
                if section.title
                    title = create_text_element(section.title)
                    center.append doc.createElement('br')
                    center.append title
                problem.append center

            else if section.type == 'linebreaks'
                text = create_text_element('')
                for i in [0..section.count] by 1
                    br = doc.createElement('br')
                    text.append(br)
                problem.append(text)

            else if section.type == 'multiple_choice'
                newel = $(doc.createElement('choiceresponse'))

                # count the number of correct choices
                num_correct = 0
                for choice in section.choices
                    if choice.correct
                        num_correct += 1 

                if num_correct == 1
                    group = $(doc.createElement('radiogroup'))
                else if num_correct > 1
                    group = $(doc.createElement('checkboxgroup'))
                newel.append(group)

                for choice_def in section.choices
                    choice = $(doc.createElement('choice'))
                    choice.attr 'correct', choice_def.correct
                    choice.append create_text_element(choice_def.text)
                    group.append(choice)

                problem.append(newel)

            else if section.type == 'numerical'
                newel = $(doc.createElement('numericalresponse'))
                newel.attr 'answer', variable_name_wrapper(section.answer)

                tolerance = $(doc.createElement('responseparam'))
                tolerance.attr 'type', 'tolerance'
                if section.tolerance == undefined
                    section.tolerance = "5%"
                tolerance.attr 'default', section.tolerance
                tolerance.attr 'name', 'tol'
                tolerance.attr 'description', 'Numerical Tolerance'
                newel.append tolerance
                newel.append doc.createElement('textline') 
                problem.append(newel)

            else if section.type == 'string'
                newel = $(doc.createElement('stringresponse'))
                newel.attr 'answer', variable_name_wrapper(section.answer)

                newel.append doc.createElement('textline') 
                problem.append(newel)

            else if section.type == 'formula'
                formularesponse = $(doc.createElement("formularesponse"))
                formularesponse.attr 'samples', section.samples
                formularesponse.attr 'answer', variable_name_wrapper(section.answer)
                formularesponse.attr 'type', 'cs'

                tolerance = $(doc.createElement('responseparam'))
                tolerance.attr 'type', 'tolerance'
                if section.tolerance == undefined
                    section.tolerance = "5%"
                tolerance.attr 'default', section.tolerance
                tolerance.attr 'name', 'tol'
                tolerance.attr 'description', 'Numerical Tolerance'

                formularesponse.append tolerance
                formularesponse.append doc.createElement('textline')
                problem.append(formularesponse)

            else
                throw new SyntaxError("unexpected section type " + section.type) 


        capa = @dom2capa(doc)
        return capa