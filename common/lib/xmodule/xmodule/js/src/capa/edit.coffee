class @CapaDescriptor
    constructor: (@element) ->
        @edit_box = $(".edit-box.capa-box", @element)
        @source_box = $(".edit-box.source-box", @element)
        @message_box = $(".parser-message-box", @element)
        @buildParser()
        @source_box.keyup =>
            @parse()

    save: -> @edit_box.val()

    buildParser: ->
        $.get "/static/grammar.jspeg", (data) =>
            @grammar = data
            @parser = PEG.buildParser @grammar
        , "text"

    buildErrorMessage: (e) ->
        if e.line != undefined && e.column != undefined
            "Line " + e.line + ", column " + e.column + ": " + e.message
        else e.message

    parse: ->
        try
            source = @source_box.val() + "\n"
            result = @parser.parse (source)
            @outputXML(result)
            @message_box.css {"display":"none"}
        catch e 
            console.log @buildErrorMessage(e)
            @message_box.html @buildErrorMessage(e)
            @message_box.css {"display":"block"}

    outputXML: (parsed) ->
        @edit_box.val @buildXML(parsed)

    dom2capa: (node) ->
        capa = new XMLSerializer().serializeToString(node)
        capa = capa + ""
        return capa.replace(/<startouttext>/g, '<startouttext />').replace(/<\/startouttext>/g, '<endouttext />')

    buildXML: (parsed) ->
        dom_parser = new DOMParser()
        doc = dom_parser.parseFromString("<problem></problem>", "text/xml");
        problem = $(doc.getElementsByTagName('problem')[0])

        create_text_element = (content) ->
            el = $(doc.createElement('startouttext'))
            el.text content
            return el

        for section in parsed
            if section.type == 'paragraph'
                newel = create_text_element(section.text)
                problem.append(newel)

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
                newel.attr 'answer', section.answer

                newel.append doc.createElement('textline') 
                problem.append(newel)

            else if section.type == 'string'
                newel = $(doc.createElement('stringresponse'))
                newel.attr 'answer', section.answer

                newel.append doc.createElement('textline') 
                problem.append(newel)

        capa = @dom2capa(doc)
        console.log capa
        return capa