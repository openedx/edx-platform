define ["js/models/metadata", "js/collections/metadata", "js/views/metadata", "cms/js/main"],
(MetadataModel, MetadataCollection, MetadataView, main) ->
  verifyInputType = (input, expectedType) ->
      # Some browsers (e.g. FireFox) do not support the "number"
      # input type.  We can accept a "text" input instead
      # and still get acceptable behavior in the UI.
      if expectedType == 'number' and input.type != 'number'
          expectedType = 'text'
      expect(input.type).toBe(expectedType)

  describe "Test Metadata Editor", ->
      editorTemplate = readFixtures('metadata-editor.underscore')
      numberEntryTemplate = readFixtures('metadata-number-entry.underscore')
      stringEntryTemplate = readFixtures('metadata-string-entry.underscore')
      optionEntryTemplate = readFixtures('metadata-option-entry.underscore')
      listEntryTemplate = readFixtures('metadata-list-entry.underscore')
      dictEntryTemplate = readFixtures('metadata-dict-entry.underscore')

      beforeEach ->
          setFixtures($("<script>", {id: "metadata-editor-tpl", type: "text/template"}).text(editorTemplate))
          appendSetFixtures($("<script>", {id: "metadata-number-entry", type: "text/template"}).text(numberEntryTemplate))
          appendSetFixtures($("<script>", {id: "metadata-string-entry", type: "text/template"}).text(stringEntryTemplate))
          appendSetFixtures($("<script>", {id: "metadata-option-entry", type: "text/template"}).text(optionEntryTemplate))
          appendSetFixtures($("<script>", {id: "metadata-list-entry", type: "text/template"}).text(listEntryTemplate))
          appendSetFixtures($("<script>", {id: "metadata-dict-entry", type: "text/template"}).text(dictEntryTemplate))

      genericEntry = {
          default_value: 'default value',
          display_name: "Display Name",
          explicitly_set: true,
          field_name: "display_name",
          help: "Specifies the name for this component.",
          options: [],
          type: MetadataModel.GENERIC_TYPE,
          value: "Word cloud"
      }

      selectEntry = {
          default_value: "answered",
          display_name: "Show Answer",
          explicitly_set: false,
          field_name: "show_answer",
          help: "When should you show the answer",
          options: [
              {"display_name": "Always", "value": "always"},
              {"display_name": "Answered", "value": "answered"},
              {"display_name": "Never", "value": "never"}
          ],
          type: MetadataModel.SELECT_TYPE,
          value: "always"
      }

      integerEntry = {
          default_value: 6,
          display_name: "Inputs",
          explicitly_set: false,
          field_name: "num_inputs",
          help: "Number of text boxes for student to input words/sentences.",
          options: {min: 1},
          type: MetadataModel.INTEGER_TYPE,
          value: 5
      }

      floatEntry = {
          default_value: 2.7,
          display_name: "Weight",
          explicitly_set: true,
          field_name: "weight",
          help: "Weight for this problem",
          options: {min: 1.3, max:100.2, step:0.1},
          type: MetadataModel.FLOAT_TYPE,
          value: 10.2
      }

      listEntry = {
          default_value: ["a thing", "another thing"],
          display_name: "List",
          explicitly_set: false,
          field_name: "list",
          help: "A list of things.",
          options: [],
          type: MetadataModel.LIST_TYPE,
          value: ["the first display value", "the second"]
      }

      timeEntry = {
          default_value: "00:00:00",
          display_name: "Time",
          explicitly_set: true,
          field_name: "relative_time",
          help: "Specifies the name for this component.",
          options: [],
          type: MetadataModel.RELATIVE_TIME_TYPE,
          value: "12:12:12"
      }

      dictEntry = {
          default_value: {
            'en': 'English',
            'ru': 'Русский'
          },
          display_name: "New Dict",
          explicitly_set: false,
          field_name: "dict",
          help: "Specifies the name for this component.",
          type: MetadataModel.DICT_TYPE,
          value: {
            'en': 'English',
            'ru': 'Русский',
            'ua': 'Українська',
            'fr': 'Français'
          }
      }


      # Test for the editor that creates the individual views.
      describe "MetadataView.Editor creates editors for each field", ->
          beforeEach ->
              @model = new MetadataCollection(
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
                          options: [
                              {"display_name": "Always", "value": "always"},
                              {"display_name": "Answered", "value": "answered"},
                              {"display_name": "Never", "value": "never"}],
                          type: "unknown type",
                          value: null
                      },
                      listEntry,
                      timeEntry,
                      dictEntry
                  ]
              )

          it "creates child views on initialize, and sorts them alphabetically", ->
              view = new MetadataView.Editor({collection: @model})
              childModels = view.collection.models
              expect(childModels.length).toBe(8)
              # Be sure to check list view as well as other input types
              childViews = view.$el.find('.setting-input, .list-settings')
              expect(childViews.length).toBe(8)

              verifyEntry = (index, display_name, type) ->
                  expect(childModels[index].get('display_name')).toBe(display_name)
                  verifyInputType(childViews[index], type)

              verifyEntry(0, 'Display Name', 'text')
              verifyEntry(1, 'Inputs', 'number')
              verifyEntry(2, 'List', '')
              verifyEntry(3, 'New Dict', '')
              verifyEntry(4, 'Show Answer', 'select-one')
              verifyEntry(5, 'Time', 'text')
              verifyEntry(6, 'Unknown', 'text')
              verifyEntry(7, 'Weight', 'number')

          it "returns its display name", ->
              view = new MetadataView.Editor({collection: @model})
              expect(view.getDisplayName()).toBe("Word cloud")

          it "returns an empty string if there is no display name property with a valid value", ->
              view = new MetadataView.Editor({collection: new MetadataCollection()})
              expect(view.getDisplayName()).toBe("")

              view = new MetadataView.Editor({collection: new MetadataCollection([
                  {
                      default_value: null,
                      display_name: "Display Name",
                      explicitly_set: false,
                      field_name: "display_name",
                      help: "",
                      options: [],
                      type: MetadataModel.GENERIC_TYPE,
                      value: null

                  }])
              })
              expect(view.getDisplayName()).toBe("")

          it "has no modified values by default", ->
              view = new MetadataView.Editor({collection: @model})
              expect(view.getModifiedMetadataValues()).toEqual({})

          it "returns modified values only", ->
              view = new MetadataView.Editor({collection: @model})
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
          verifyInputType(input[0], expectedType)

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

      describe "MetadataView.String is a basic string input with clear functionality", ->
          beforeEach ->
              model = new MetadataModel(genericEntry)
              @view = new MetadataView.String({model: model})

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

      describe "MetadataView.Option is an option input type with clear functionality", ->
          beforeEach ->
              model = new MetadataModel(selectEntry)
              @view = new MetadataView.Option({model: model})

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

      describe "MetadataView.Number supports integer or float type and has clear functionality", ->
          verifyValueAfterChanged = (view, value, expectedResult) ->
              view.setValueInEditor(value)
              view.changed()
              expect(view.getValueFromEditor()).toBe(expectedResult)

          beforeEach ->
              integerModel = new MetadataModel(integerEntry)
              @integerView = new MetadataView.Number({model: integerModel})

              floatModel = new MetadataModel(floatEntry)
              @floatView = new MetadataView.Number({model: floatModel})

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
              assertClear(@integerView, 6, '6')
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
              verifyValueAfterChanged(@integerView, '-4', '1')
              verifyValueAfterChanged(@integerView, '1', '1')
              verifyValueAfterChanged(@integerView, '0', '1')
              verifyValueAfterChanged(@integerView, '3001', '3001')

              verifyValueAfterChanged(@floatView, '-4', '1.3')
              verifyValueAfterChanged(@floatView, '1.3', '1.3')
              verifyValueAfterChanged(@floatView, '1.2', '1.3')
              verifyValueAfterChanged(@floatView, '100.2', '100.2')
              verifyValueAfterChanged(@floatView, '100.3', '100.2')

          it "sets default values for integer and float fields that are empty", ->
              verifyValueAfterChanged(@integerView, '', '6')
              verifyValueAfterChanged(@floatView, '', '2.7')

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

      describe "MetadataView.List allows the user to enter an ordered list of strings", ->
        beforeEach ->
          listModel = new MetadataModel(listEntry)
          @listView = new MetadataView.List({model: listModel})
          @el = @listView.$el
          main()

        it "returns the initial value upon initialization", ->
          assertValueInView(@listView, ['the first display value', 'the second'])

        it "updates its value correctly", ->
          assertCanUpdateView(@listView, ['a new item', 'another new item', 'a third'])

        it "has a clear method to revert to the model default", ->
          @el.find('.create-setting').click()
          assertClear(@listView, ['a thing', 'another thing'])
          expect(@el.find('.create-setting')).not.toHaveClass('is-disabled')

        it "has an update model method", ->
          assertUpdateModel(@listView, null, ['a new value'])

        it "can add an entry", ->
          expect(@listView.model.get('value').length).toEqual(2)
          @el.find('.create-setting').click()
          expect(@el.find('input.input').length).toEqual(3)

        it "can remove an entry", ->
          expect(@listView.model.get('value').length).toEqual(2)
          @el.find('.remove-setting').first().click()
          expect(@listView.model.get('value').length).toEqual(1)

        it "only allows one blank entry at a time", ->
          expect(@el.find('input').length).toEqual(2)
          @el.find('.create-setting').click()
          @el.find('.create-setting').click()
          expect(@el.find('input').length).toEqual(3)

        it "re-enables the add setting button after entering a new value", ->
          expect(@el.find('input').length).toEqual(2)
          @el.find('.create-setting').click()
          expect(@el.find('.create-setting')).toHaveClass('is-disabled')
          @el.find('input').last().val('third setting')
          @el.find('input').last().trigger('input')
          expect(@el.find('.create-setting')).not.toHaveClass('is-disabled')

      describe "MetadataView.RelativeTime allows the user to enter time string in HH:mm:ss format", ->
          beforeEach ->
              model = new MetadataModel(timeEntry)
              @view = new MetadataView.RelativeTime({model: model})

          it "uses a text input type", ->
              assertInputType(@view, 'text')

          it "returns the intial value upon initialization", ->
              assertValueInView(@view, '12:12:12')

          it "value is converted correctly", ->
            view = @view

            cases = [
              {
                input: '23:100:0'
                output: '23:59:59'
              },
              {
                input: '100000000000000000'
                output: '23:59:59'
              },
              {
                input: '80000'
                output: '22:13:20'
              },
              {
                input: '-100'
                output: '00:00:00'
              },
              {
                input: '-100:-10'
                output: '00:00:00'
              },
              {
                input: '99:99'
                output: '01:40:39'
              },
              {
                input: '2'
                output: '00:00:02'
              },
              {
                input: '1:2'
                output: '00:01:02'
              },
              {
                input: '1:25'
                output: '00:01:25'
              },
              {
                input: '3:1:25'
                output: '03:01:25'
              },
              {
                input: ' 2 3 : 5 9 : 5 9 '
                output: '23:59:59'
              },
              {
                input: '9:1:25'
                output: '09:01:25'
              },
              {
                input: '77:72:77'
                output: '23:59:59'
              },
              {
                input: '22:100:100'
                output: '23:41:40'
              },
              # negative value
              {
                input: '-22:22:22'
                output: '00:22:22'
              },
              # simple string
              {
                input: 'simple text'
                output: '00:00:00'
              },
              {
                input: 'a10a:a10a:a10a'
                output: '00:00:00'
              },
              # empty string
              {
                input: ''
                output: '00:00:00'
              }
            ]

            $.each cases, (index, data) ->
                expect(view.parseRelativeTime(data.input)).toBe(data.output)

          it "can update its value in the view", ->
              assertCanUpdateView(@view, "23:59:59")
              @view.setValueInEditor("33:59:59")
              @view.updateModel()
              assertValueInView(@view, "23:59:59")

          it "has a clear method to revert to the model default", ->
              assertClear(@view, '00:00:00')

          it "has an update model method", ->
              assertUpdateModel(@view, '12:12:12', '23:59:59')

      describe "MetadataView.Dict allows the user to enter key-value pairs of strings", ->
        beforeEach ->
          dictModel = new MetadataModel($.extend(true, {}, dictEntry))
          @dictView = new MetadataView.Dict({model: dictModel})
          @el = @dictView.$el
          main()

        it "returns the initial value upon initialization", ->
          assertValueInView(@dictView, {
            'en': 'English',
            'ru': 'Русский',
            'ua': 'Українська',
            'fr': 'Français'
          })

        it "updates its value correctly", ->
          assertCanUpdateView(@dictView, {
            'ru': 'Русский',
            'ua': 'Українська',
            'fr': 'Français'
          })

        it "has a clear method to revert to the model default", ->
          @el.find('.create-setting').click()
          assertClear(@dictView, {
            'en': 'English',
            'ru': 'Русский'
          })
          expect(@el.find('.create-setting')).not.toHaveClass('is-disabled')

        it "has an update model method", ->
          assertUpdateModel(@dictView, null, {'fr': 'Français'})

        it "can add an entry", ->
          expect(_.keys(@dictView.model.get('value')).length).toEqual(4)
          @el.find('.create-setting').click()
          expect(@el.find('input.input-key').length).toEqual(5)

        it "can remove an entry", ->
          expect(_.keys(@dictView.model.get('value')).length).toEqual(4)
          @el.find('.remove-setting').first().click()
          expect(_.keys(@dictView.model.get('value')).length).toEqual(3)

        it "only allows one blank entry at a time", ->
          expect(@el.find('input.input-key').length).toEqual(4)
          @el.find('.create-setting').click()
          @el.find('.create-setting').click()
          expect(@el.find('input.input-key').length).toEqual(5)

        it "only allows unique keys", ->
          data = [
            {
              expectedValue: {'ru': 'Русский'},
              initialValue: {'ru': 'Русский'},
              testValue: {
                'key': 'ru'
                'value': ''
              }
            },
            {
              expectedValue: {'ru': 'Русский'},
              initialValue: {'ru': 'Some value'},
              testValue: {
                'key': 'ru'
                'value': 'Русский'
              }
            },
            {
              expectedValue: {'ru': 'Русский'},
              initialValue: {'ru': 'Русский'},
              testValue: {
                'key': ''
                'value': ''
              }
            }
          ]

          _.each data, ((d, index) ->
            @dictView.setValueInEditor(d.initialValue)
            @dictView.updateModel();
            @el.find('.create-setting').click()
            item = @el.find('.list-settings-item').last()
            item.find('.input-key').val(d.testValue.key);
            item.find('.input-value').val(d.testValue.value);

            expect(@dictView.getValueFromEditor()).toEqual(d.expectedValue)
          ).bind(@)

        it "re-enables the add setting button after entering a new value", ->
          expect(@el.find('input.input-key').length).toEqual(4)
          @el.find('.create-setting').click()
          expect(@el.find('.create-setting')).toHaveClass('is-disabled')
          @el.find('input.input-key').last().val('third setting')
          @el.find('input.input-key').last().trigger('input')
          expect(@el.find('.create-setting')).not.toHaveClass('is-disabled')
