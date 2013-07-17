describe "Test Metadata Editor", ->
    editorTemplate = readFixtures('metadata-editor.underscore')
    numberEntryTemplate = readFixtures('metadata-number-entry.underscore')
    stringEntryTemplate = readFixtures('metadata-string-entry.underscore')
    optionEntryTemplate = readFixtures('metadata-option-entry.underscore')
    listEntryTemplate = readFixtures('metadata-list-entry.underscore')

    beforeEach ->
        setFixtures($("<script>", {id: "metadata-editor-tpl", type: "text/template"}).text(editorTemplate))
        appendSetFixtures($("<script>", {id: "metadata-number-entry", type: "text/template"}).text(numberEntryTemplate))
        appendSetFixtures($("<script>", {id: "metadata-string-entry", type: "text/template"}).text(stringEntryTemplate))
        appendSetFixtures($("<script>", {id: "metadata-option-entry", type: "text/template"}).text(optionEntryTemplate))
        appendSetFixtures($("<script>", {id: "metadata-list-entry", type: "text/template"}).text(listEntryTemplate))

    genericEntry = {
        default_value: 'default value',
        display_name: "Display Name",
        explicitly_set: true,
        field_name: "display_name",
        help: "Specifies the name for this component.",
        inheritable: false,
        options: [],
        type: CMS.Models.Metadata.GENERIC_TYPE,
        value: "Word cloud"
    }

    selectEntry = {
        default_value: "answered",
        display_name: "Show Answer",
        explicitly_set: false,
        field_name: "show_answer",
        help: "When should you show the answer",
        inheritable: true,
        options: [
            {"display_name": "Always", "value": "always"},
            {"display_name": "Answered", "value": "answered"},
            {"display_name": "Never", "value": "never"}
        ],
        type: CMS.Models.Metadata.SELECT_TYPE,
        value: "always"
    }

    integerEntry = {
        default_value: 5,
        display_name: "Inputs",
        explicitly_set: false,
        field_name: "num_inputs",
        help: "Number of text boxes for student to input words/sentences.",
        inheritable: false,
        options: {min: 1},
        type: CMS.Models.Metadata.INTEGER_TYPE,
        value: 5
    }

    floatEntry = {
        default_value: 2.7,
        display_name: "Weight",
        explicitly_set: true,
        field_name: "weight",
        help: "Weight for this problem",
        inheritable: true,
        options: {min: 1.3, max:100.2, step:0.1},
        type: CMS.Models.Metadata.FLOAT_TYPE,
        value: 10.2
    }

    listEntry = {
        default_value: ["a thing", "another thing"],
        display_name: "List",
        explicitly_set: false,
        field_name: "list",
        help: "A list of things.",
        inheritable: false,
        options: [],
        type: CMS.Models.Metadata.LIST_TYPE,
        value: ["the first display value", "the second"]
    }

    # Test for the editor that creates the individual views.
    describe "CMS.Views.Metadata.Editor creates editors for each field", ->
        beforeEach ->
            @model = new CMS.Models.MetadataCollection(
                [
                    integerEntry,
                    floatEntry,
                    selectEntry,
                    genericEntry,
                    {
                        default_value: null,
                        display_name: "Unknown",
                        explicitly_set: true,
                        field_name: "unknown_type",
                        help: "Mystery property.",
                        inheritable: false,
                        options: [
                            {"display_name": "Always", "value": "always"},
                            {"display_name": "Answered", "value": "answered"},
                            {"display_name": "Never", "value": "never"}],
                        type: "unknown type",
                        value: null
                    },
                    listEntry
                ]
            )

        it "creates child views on initialize, and sorts them alphabetically", ->
            view = new CMS.Views.Metadata.Editor({collection: @model})
            childModels = view.collection.models
            expect(childModels.length).toBe(6)
            childViews = view.$el.find('.setting-input')
            expect(childViews.length).toBe(6)

            verifyEntry = (index, display_name, type) ->
                expect(childModels[index].get('display_name')).toBe(display_name)
                expect(childViews[index].type).toBe(type)

            verifyEntry(0, 'Display Name', 'text')
            verifyEntry(1, 'Inputs', 'number')
            verifyEntry(2, 'List', 'text')
            verifyEntry(3, 'Show Answer', 'select-one')
            verifyEntry(4, 'Unknown', 'text')
            verifyEntry(5, 'Weight', 'number')

        it "returns its display name", ->
            view = new CMS.Views.Metadata.Editor({collection: @model})
            expect(view.getDisplayName()).toBe("Word cloud")

        it "returns an empty string if there is no display name property with a valid value", ->
            view = new CMS.Views.Metadata.Editor({collection: new CMS.Models.MetadataCollection()})
            expect(view.getDisplayName()).toBe("")

            view = new CMS.Views.Metadata.Editor({collection: new CMS.Models.MetadataCollection([
                {
                    default_value: null,
                    display_name: "Display Name",
                    explicitly_set: false,
                    field_name: "display_name",
                    help: "",
                    inheritable: false,
                    options: [],
                    type: CMS.Models.Metadata.GENERIC_TYPE,
                    value: null

                }])
            })
            expect(view.getDisplayName()).toBe("")

        it "has no modified values by default", ->
            view = new CMS.Views.Metadata.Editor({collection: @model})
            expect(view.getModifiedMetadataValues()).toEqual({})

        it "returns modified values only", ->
            view = new CMS.Views.Metadata.Editor({collection: @model})
            childModels = view.collection.models
            childModels[0].setValue('updated display name')
            childModels[1].setValue(20)
            expect(view.getModifiedMetadataValues()).toEqual({
                display_name : 'updated display name',
                num_inputs: 20
            })

    # Tests for individual views.
    assertInputType = (view, expectedType) ->
        input = view.$el.find('.setting-input')
        expect(input.length).toEqual(1)
        expect(input[0].type).toEqual(expectedType)

    assertValueInView = (view, expectedValue) ->
        expect(view.getValueFromEditor()).toEqual(expectedValue)

    assertCanUpdateView = (view, newValue) ->
        view.setValueInEditor(newValue)
        expect(view.getValueFromEditor()).toEqual(newValue)

    assertClear = (view, modelValue, editorValue=modelValue) ->
        view.clear()
        expect(view.model.getValue()).toBe(null)
        expect(view.model.getDisplayValue()).toEqual(modelValue)
        expect(view.getValueFromEditor()).toEqual(editorValue)

    assertUpdateModel = (view, originalValue, newValue) ->
        view.setValueInEditor(newValue)
        expect(view.model.getValue()).toEqual(originalValue)
        view.updateModel()
        expect(view.model.getValue()).toEqual(newValue)

    describe "CMS.Views.Metadata.String is a basic string input with clear functionality", ->
        beforeEach ->
            model = new CMS.Models.Metadata(genericEntry)
            @view = new CMS.Views.Metadata.String({model: model})

        it "uses a text input type", ->
            assertInputType(@view, 'text')

        it "returns the intial value upon initialization", ->
            assertValueInView(@view, 'Word cloud')

        it "can update its value in the view", ->
            assertCanUpdateView(@view, "updated ' \" &")

        it "has a clear method to revert to the model default", ->
            assertClear(@view, 'default value')

        it "has an update model method", ->
            assertUpdateModel(@view, 'Word cloud', 'updated')

    describe "CMS.Views.Metadata.Option is an option input type with clear functionality", ->
        beforeEach ->
            model = new CMS.Models.Metadata(selectEntry)
            @view = new CMS.Views.Metadata.Option({model: model})

        it "uses a select input type", ->
            assertInputType(@view, 'select-one')

        it "returns the intial value upon initialization", ->
            assertValueInView(@view, 'always')

        it "can update its value in the view", ->
            assertCanUpdateView(@view, "never")

        it "has a clear method to revert to the model default", ->
            assertClear(@view, 'answered')

        it "has an update model method", ->
            assertUpdateModel(@view, null, 'never')

        it "does not update to a value that is not an option", ->
            @view.setValueInEditor("not an option")
            expect(@view.getValueFromEditor()).toBe('always')

    describe "CMS.Views.Metadata.Number supports integer or float type and has clear functionality", ->
        beforeEach ->
            integerModel = new CMS.Models.Metadata(integerEntry)
            @integerView = new CMS.Views.Metadata.Number({model: integerModel})

            floatModel = new CMS.Models.Metadata(floatEntry)
            @floatView = new CMS.Views.Metadata.Number({model: floatModel})

        it "uses a number input type", ->
            assertInputType(@integerView, 'number')
            assertInputType(@floatView, 'number')

        it "returns the intial value upon initialization", ->
            assertValueInView(@integerView, '5')
            assertValueInView(@floatView, '10.2')

        it "can update its value in the view", ->
            assertCanUpdateView(@integerView, "12")
            assertCanUpdateView(@floatView, "-2.4")

        it "has a clear method to revert to the model default", ->
            assertClear(@integerView, 5, '5')
            assertClear(@floatView, 2.7, '2.7')

        it "has an update model method", ->
            assertUpdateModel(@integerView, null, '90')
            assertUpdateModel(@floatView, 10.2, '-9.5')

        it "knows the difference between integer and float", ->
            expect(@integerView.isIntegerField()).toBeTruthy()
            expect(@floatView.isIntegerField()).toBeFalsy()

        it "sets attribtues related to min, max, and step", ->
            verifyAttributes = (view, min, step, max=null) ->
                inputEntry =  view.$el.find('input')
                expect(Number(inputEntry.attr('min'))).toEqual(min)
                expect(Number(inputEntry.attr('step'))).toEqual(step)
                if max is not null
                    expect(Number(inputEntry.attr('max'))).toEqual(max)

            verifyAttributes(@integerView, 1, 1)
            verifyAttributes(@floatView, 1.3, .1, 100.2)

        it "corrects values that are out of range", ->
            verifyValueAfterChanged = (view, value, expectedResult) ->
                view.setValueInEditor(value)
                view.changed()
                expect(view.getValueFromEditor()).toBe(expectedResult)

            verifyValueAfterChanged(@integerView, '-4', '1')
            verifyValueAfterChanged(@integerView, '1', '1')
            verifyValueAfterChanged(@integerView, '0', '1')
            verifyValueAfterChanged(@integerView, '3001', '3001')

            verifyValueAfterChanged(@floatView, '-4', '1.3')
            verifyValueAfterChanged(@floatView, '1.3', '1.3')
            verifyValueAfterChanged(@floatView, '1.2', '1.3')
            verifyValueAfterChanged(@floatView, '100.2', '100.2')
            verifyValueAfterChanged(@floatView, '100.3', '100.2')

        it "disallows invalid characters", ->
            verifyValueAfterKeyPressed = (view, character, reject) ->
                event = {
                    type : 'keypress',
                    which : character.charCodeAt(0),
                    keyCode:  character.charCodeAt(0),
                    preventDefault : () -> 'no op'
                }
                spyOn(event, 'preventDefault')
                view.$el.find('input').trigger(event)
                if (reject)
                    expect(event.preventDefault).toHaveBeenCalled()
                else
                    expect(event.preventDefault).not.toHaveBeenCalled()

            verifyDisallowedChars = (view) ->
                verifyValueAfterKeyPressed(view, 'a', true)
                verifyValueAfterKeyPressed(view, '.', view.isIntegerField())
                verifyValueAfterKeyPressed(view, '[', true)
                verifyValueAfterKeyPressed(view, '@', true)

                for i in [0...9]
                    verifyValueAfterKeyPressed(view, String(i), false)

            verifyDisallowedChars(@integerView)
            verifyDisallowedChars(@floatView)

    describe "CMS.Views.Metadata.List allows the user to enter an ordered list of strings", ->
      beforeEach ->
        listModel = new CMS.Models.Metadata(listEntry)
        @listView = new CMS.Views.Metadata.List({model: listModel})

      it "uses a text input type", ->
        assertInputType(@listView, 'text')

      it "returns the initial value upon initialization", ->
        assertValueInView(@listView, ['the first display value', 'the second'])

      it "updates its value correctly", ->
        assertCanUpdateView(@listView, ['a new item', 'another new item', 'a third'])

      it "has a clear method to revert to the model default", ->
        assertClear(@listView, ['a thing', 'another thing'])

      it "has an update model method", ->
        assertUpdateModel(@listView, null, ['a new value'])
