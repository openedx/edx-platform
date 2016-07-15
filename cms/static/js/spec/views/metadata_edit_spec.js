(function() {
    'use strict';
    define(['js/models/metadata', 'js/collections/metadata', 'js/views/metadata', 'js/main'],
           function(MetadataModel, MetadataCollection, MetadataView, main) {
        var verifyInputType;
        verifyInputType = function(input, expectedType) {
            if (expectedType === 'number' && input.type !== 'number') {
                expectedType = 'text';
            }
            expect(input.type).toBe(expectedType);
        };
        describe('Test Metadata Editor', function() {
            var assertCanUpdateView, assertClear, assertInputType, assertUpdateModel, assertValueInView,
                dictEntry, dictEntryTemplate, editorTemplate, floatEntry, genericEntry, integerEntry,
                listEntry, listEntryTemplate, numberEntryTemplate, optionEntryTemplate, selectEntry,
                stringEntryTemplate, timeEntry;
            editorTemplate = readFixtures('metadata-editor.underscore');
            numberEntryTemplate = readFixtures('metadata-number-entry.underscore');
            stringEntryTemplate = readFixtures('metadata-string-entry.underscore');
            optionEntryTemplate = readFixtures('metadata-option-entry.underscore');
            listEntryTemplate = readFixtures('metadata-list-entry.underscore');
            dictEntryTemplate = readFixtures('metadata-dict-entry.underscore');
            beforeEach(function() {
                setFixtures($('<script>', {
                    id: 'metadata-editor-tpl',
                    type: 'text/template'
                }).text(editorTemplate));
                appendSetFixtures($('<script>', {
                    id: 'metadata-number-entry',
                    type: 'text/template'
                }).text(numberEntryTemplate));
                appendSetFixtures($('<script>', {
                    id: 'metadata-string-entry',
                    type: 'text/template'
                }).text(stringEntryTemplate));
                appendSetFixtures($('<script>', {
                    id: 'metadata-option-entry',
                    type: 'text/template'
                }).text(optionEntryTemplate));
                appendSetFixtures($('<script>', {
                    id: 'metadata-list-entry',
                    type: 'text/template'
                }).text(listEntryTemplate));
                appendSetFixtures($('<script>', {
                    id: 'metadata-dict-entry',
                    type: 'text/template'
                }).text(dictEntryTemplate));
            });
            genericEntry = {
                default_value: 'default value',
                display_name: 'Display Name',
                explicitly_set: true,
                field_name: 'display_name',
                help: 'Specifies the name for this component.',
                options: [],
                type: MetadataModel.GENERIC_TYPE,
                value: 'Word cloud'
            };
            selectEntry = {
                default_value: 'answered',
                display_name: 'Show Answer',
                explicitly_set: false,
                field_name: 'show_answer',
                help: 'When should you show the answer',
                options: [
                    {
                        'display_name': 'Always',
                        'value': 'always'
                    }, {
                        'display_name': 'Answered',
                        'value': 'answered'
                    }, {
                        'display_name': 'Never',
                        'value': 'never'
                    }
                ],
                type: MetadataModel.SELECT_TYPE,
                value: 'always'
            };
            integerEntry = {
                default_value: 6,
                display_name: 'Inputs',
                explicitly_set: false,
                field_name: 'num_inputs',
                help: 'Number of text boxes for student to input words/sentences.',
                options: {
                    min: 1
                },
                type: MetadataModel.INTEGER_TYPE,
                value: 5
            };
            floatEntry = {
                default_value: 2.7,
                display_name: 'Weight',
                explicitly_set: true,
                field_name: 'weight',
                help: 'Weight for this problem',
                options: {
                    min: 1.3,
                    max: 100.2,
                    step: 0.1
                },
                type: MetadataModel.FLOAT_TYPE,
                value: 10.2
            };
            listEntry = {
                default_value: ['a thing', 'another thing'],
                display_name: 'List',
                explicitly_set: false,
                field_name: 'list',
                help: 'A list of things.',
                options: [],
                type: MetadataModel.LIST_TYPE,
                value: ['the first display value', 'the second']
            };
            timeEntry = {
                default_value: '00:00:00',
                display_name: 'Time',
                explicitly_set: true,
                field_name: 'relative_time',
                help: 'Specifies the name for this component.',
                options: [],
                type: MetadataModel.RELATIVE_TIME_TYPE,
                value: '12:12:12'
            };
            dictEntry = {
                default_value: {
                    'en': 'English',
                    'ru': 'Русский'
                },
                display_name: 'New Dict',
                explicitly_set: false,
                field_name: 'dict',
                help: 'Specifies the name for this component.',
                type: MetadataModel.DICT_TYPE,
                value: {
                    'en': 'English',
                    'ru': 'Русский',
                    'ua': 'Українська',
                    'fr': 'Français'
                }
            };
            describe('MetadataView.Editor creates editors for each field', function() {
                beforeEach(function() {
                    this.model = new MetadataCollection([
                        integerEntry, floatEntry, selectEntry, genericEntry, {
                            default_value: null,
                            display_name: 'Unknown',
                            explicitly_set: true,
                            field_name: 'unknown_type',
                            help: 'Mystery property.',
                            options: [
                                {
                                    'display_name': 'Always',
                                    'value': 'always'
                                }, {
                                    'display_name': 'Answered',
                                    'value': 'answered'
                                }, {
                                    'display_name': 'Never',
                                    'value': 'never'
                                }
                            ],
                            type: 'unknown type',
                            value: null
                        }, listEntry, timeEntry, dictEntry
                    ]);
                });
                it('creates child views on initialize, and sorts them alphabetically', function() {
                    var childModels, childViews, verifyEntry, view;
                    view = new MetadataView.Editor({
                        collection: this.model
                    });
                    childModels = view.collection.models;
                    expect(childModels.length).toBe(8);
                    childViews = view.$el.find('.setting-input, .list-settings');
                    expect(childViews.length).toBe(8);
                    verifyEntry = function(index, display_name, type) {
                        expect(childModels[index].get('display_name')).toBe(display_name);
                        verifyInputType(childViews[index], type);
                    };
                    verifyEntry(0, 'Display Name', 'text');
                    verifyEntry(1, 'Inputs', 'number');
                    verifyEntry(2, 'List', '');
                    verifyEntry(3, 'New Dict', '');
                    verifyEntry(4, 'Show Answer', 'select-one');
                    verifyEntry(5, 'Time', 'text');
                    verifyEntry(6, 'Unknown', 'text');
                    verifyEntry(7, 'Weight', 'number');
                });
                it('returns its display name', function() {
                    var view;
                    view = new MetadataView.Editor({
                        collection: this.model
                    });
                    expect(view.getDisplayName()).toBe('Word cloud');
                });
                it('returns an empty string if there is no display name property with a valid value', function() {
                    var view;
                    view = new MetadataView.Editor({
                        collection: new MetadataCollection()
                    });
                    expect(view.getDisplayName()).toBe('');
                    view = new MetadataView.Editor({
                        collection: new MetadataCollection([
                            {
                                default_value: null,
                                display_name: 'Display Name',
                                explicitly_set: false,
                                field_name: 'display_name',
                                help: '',
                                options: [],
                                type: MetadataModel.GENERIC_TYPE,
                                value: null
                            }
                        ])
                    });
                    expect(view.getDisplayName()).toBe('');
                });
                it('has no modified values by default', function() {
                    var view;
                    view = new MetadataView.Editor({
                        collection: this.model
                    });
                    expect(view.getModifiedMetadataValues()).toEqual({});
                });
                it('returns modified values only', function() {
                    var childModels, view;
                    view = new MetadataView.Editor({
                        collection: this.model
                    });
                    childModels = view.collection.models;
                    childModels[0].setValue('updated display name');
                    childModels[1].setValue(20);
                    expect(view.getModifiedMetadataValues()).toEqual({
                        display_name: 'updated display name',
                        num_inputs: 20
                    });
                });
            });
            assertInputType = function(view, expectedType) {
                var input;
                input = view.$el.find('.setting-input');
                expect(input.length).toEqual(1);
                verifyInputType(input[0], expectedType);
            };
            assertValueInView = function(view, expectedValue) {
                expect(view.getValueFromEditor()).toEqual(expectedValue);
            };
            assertCanUpdateView = function(view, newValue) {
                view.setValueInEditor(newValue);
                expect(view.getValueFromEditor()).toEqual(newValue);
            };
            assertClear = function(view, modelValue, editorValue) {
                if (!editorValue) {
                    editorValue = modelValue;
                }
                view.clear();
                expect(view.model.getValue()).toBe(null);
                expect(view.model.getDisplayValue()).toEqual(modelValue);
                expect(view.getValueFromEditor()).toEqual(editorValue);
            };
            assertUpdateModel = function(view, originalValue, newValue) {
                view.setValueInEditor(newValue);
                expect(view.model.getValue()).toEqual(originalValue);
                view.updateModel();
                expect(view.model.getValue()).toEqual(newValue);
            };
            describe('MetadataView.String is a basic string input with clear functionality', function() {
                beforeEach(function() {
                    var model;
                    model = new MetadataModel(genericEntry);
                    this.view = new MetadataView.String({
                        model: model
                    });
                });
                it('uses a text input type', function() {
                    assertInputType(this.view, 'text');
                });
                it('returns the intial value upon initialization', function() {
                    assertValueInView(this.view, 'Word cloud');
                });
                it('can update its value in the view', function() {
                    assertCanUpdateView(this.view, "updated ' \" &");
                });
                it('has a clear method to revert to the model default', function() {
                    assertClear(this.view, 'default value');
                });
                it('has an update model method', function() {
                    assertUpdateModel(this.view, 'Word cloud', 'updated');
                });
            });
            describe('MetadataView.Option is an option input type with clear functionality', function() {
                beforeEach(function() {
                    var model;
                    model = new MetadataModel(selectEntry);
                    this.view = new MetadataView.Option({
                        model: model
                    });
                });
                it('uses a select input type', function() {
                    assertInputType(this.view, 'select-one');
                });
                it('returns the intial value upon initialization', function() {
                    assertValueInView(this.view, 'always');
                });
                it('can update its value in the view', function() {
                    assertCanUpdateView(this.view, 'never');
                });
                it('has a clear method to revert to the model default', function() {
                    assertClear(this.view, 'answered');
                });
                it('has an update model method', function() {
                    assertUpdateModel(this.view, null, 'never');
                });
                it('does not update to a value that is not an option', function() {
                    this.view.setValueInEditor('not an option');
                    expect(this.view.getValueFromEditor()).toBe('always');
                });
            });
            describe('MetadataView.Number supports integer or float type and has clear functionality', function() {
                var verifyValueAfterChanged;
                verifyValueAfterChanged = function(view, value, expectedResult) {
                    view.setValueInEditor(value);
                    view.changed();
                    expect(view.getValueFromEditor()).toBe(expectedResult);
                };
                beforeEach(function() {
                    var floatModel, integerModel;
                    integerModel = new MetadataModel(integerEntry);
                    this.integerView = new MetadataView.Number({
                        model: integerModel
                    });
                    floatModel = new MetadataModel(floatEntry);
                    this.floatView = new MetadataView.Number({
                        model: floatModel
                    });
                });
                it('uses a number input type', function() {
                    assertInputType(this.integerView, 'number');
                    assertInputType(this.floatView, 'number');
                });
                it('returns the intial value upon initialization', function() {
                    assertValueInView(this.integerView, '5');
                    assertValueInView(this.floatView, '10.2');
                });
                it('can update its value in the view', function() {
                    assertCanUpdateView(this.integerView, '12');
                    assertCanUpdateView(this.floatView, '-2.4');
                });
                it('has a clear method to revert to the model default', function() {
                    assertClear(this.integerView, 6, '6');
                    assertClear(this.floatView, 2.7, '2.7');
                });
                it('has an update model method', function() {
                    assertUpdateModel(this.integerView, null, '90');
                    assertUpdateModel(this.floatView, 10.2, '-9.5');
                });
                it('knows the difference between integer and float', function() {
                    expect(this.integerView.isIntegerField()).toBeTruthy();
                    expect(this.floatView.isIntegerField()).toBeFalsy();
                });
                it('sets attribtues related to min, max, and step', function() {
                    var verifyAttributes;
                    verifyAttributes = function(view, min, step, max) {
                        var inputEntry;
                        if (!max) {
                            max = null;
                        }
                        inputEntry = view.$el.find('input');
                        expect(Number(inputEntry.attr('min'))).toEqual(min);
                        expect(Number(inputEntry.attr('step'))).toEqual(step);
                        if (max) {
                            expect(Number(inputEntry.attr('max'))).toEqual(max);
                        }
                    };
                    verifyAttributes(this.integerView, 1, 1);
                    verifyAttributes(this.floatView, 1.3, 0.1, 100.2);
                });
                it('corrects values that are out of range', function() {
                    verifyValueAfterChanged(this.integerView, '-4', '1');
                    verifyValueAfterChanged(this.integerView, '1', '1');
                    verifyValueAfterChanged(this.integerView, '0', '1');
                    verifyValueAfterChanged(this.integerView, '3001', '3001');
                    verifyValueAfterChanged(this.floatView, '-4', '1.3');
                    verifyValueAfterChanged(this.floatView, '1.3', '1.3');
                    verifyValueAfterChanged(this.floatView, '1.2', '1.3');
                    verifyValueAfterChanged(this.floatView, '100.2', '100.2');
                    verifyValueAfterChanged(this.floatView, '100.3', '100.2');
                });
                it('sets default values for integer and float fields that are empty', function() {
                    verifyValueAfterChanged(this.integerView, '', '6');
                    verifyValueAfterChanged(this.floatView, '', '2.7');
                });
                it('disallows invalid characters', function() {
                    var verifyDisallowedChars, verifyValueAfterKeyPressed;
                    verifyValueAfterKeyPressed = function(view, character, reject) {
                        var event;
                        event = {
                            type: 'keypress',
                            which: character.charCodeAt(0),
                            keyCode: character.charCodeAt(0),
                            preventDefault: function() {
                                return 'no op';
                            }
                        };
                        spyOn(event, 'preventDefault');
                        view.$el.find('input').trigger(event);
                        if (reject) {
                            expect(event.preventDefault).toHaveBeenCalled();
                        } else {
                            expect(event.preventDefault).not.toHaveBeenCalled();
                        }
                    };
                    verifyDisallowedChars = function(view) {
                        var i, _i, _results;
                        verifyValueAfterKeyPressed(view, 'a', true);
                        verifyValueAfterKeyPressed(view, '.', view.isIntegerField());
                        verifyValueAfterKeyPressed(view, '[', true);
                        verifyValueAfterKeyPressed(view, '@', true);
                        _results = [];
                        for (i = _i = 0; _i < 9; i = ++_i) {
                            _results.push(verifyValueAfterKeyPressed(view, String(i), false));
                        }
                        return _results;
                    };
                    verifyDisallowedChars(this.integerView);
                    return verifyDisallowedChars(this.floatView);
                });
            });
            describe('MetadataView.List allows the user to enter an ordered list of strings', function() {
                beforeEach(function() {
                    var listModel;
                    listModel = new MetadataModel(listEntry);
                    this.listView = new MetadataView.List({
                        model: listModel
                    });
                    this.el = this.listView.$el;
                    return main();
                });
                it('returns the initial value upon initialization', function() {
                    assertValueInView(this.listView, ['the first display value', 'the second']);
                });
                it('updates its value correctly', function() {
                    assertCanUpdateView(this.listView, ['a new item', 'another new item', 'a third']);
                });
                it('has a clear method to revert to the model default', function() {
                    this.el.find('.create-setting').click();
                    assertClear(this.listView, ['a thing', 'another thing']);
                    expect(this.el.find('.create-setting')).not.toHaveClass('is-disabled');
                });
                it('has an update model method', function() {
                    assertUpdateModel(this.listView, null, ['a new value']);
                });
                it('can add an entry', function() {
                    expect(this.listView.model.get('value').length).toEqual(2);
                    this.el.find('.create-setting').click();
                    expect(this.el.find('input.input').length).toEqual(3);
                });
                it('can remove an entry', function() {
                    expect(this.listView.model.get('value').length).toEqual(2);
                    this.el.find('.remove-setting').first().click();
                    expect(this.listView.model.get('value').length).toEqual(1);
                });
                it('only allows one blank entry at a time', function() {
                    expect(this.el.find('input').length).toEqual(2);
                    this.el.find('.create-setting').click();
                    this.el.find('.create-setting').click();
                    expect(this.el.find('input').length).toEqual(3);
                });
                it('re-enables the add setting button after entering a new value', function() {
                    expect(this.el.find('input').length).toEqual(2);
                    this.el.find('.create-setting').click();
                    expect(this.el.find('.create-setting')).toHaveClass('is-disabled');
                    this.el.find('input').last().val('third setting');
                    this.el.find('input').last().trigger('input');
                    expect(this.el.find('.create-setting')).not.toHaveClass('is-disabled');
                });
            });
            describe('MetadataView.RelativeTime allows the user to enter time string in HH:mm:ss format', function() {
                beforeEach(function() {
                    var model;
                    model = new MetadataModel(timeEntry);
                    this.view = new MetadataView.RelativeTime({
                        model: model
                    });
                });
                it('uses a text input type', function() {
                    assertInputType(this.view, 'text');
                });
                it('returns the intial value upon initialization', function() {
                    assertValueInView(this.view, '12:12:12');
                });
                it('value is converted correctly', function() {
                    var cases, view;
                    view = this.view;
                    cases = [
                        {
                            input: '23:100:0',
                            output: '23:59:59'
                        }, {
                            input: '100000000000000000',
                            output: '23:59:59'
                        }, {
                            input: '80000',
                            output: '22:13:20'
                        }, {
                            input: '-100',
                            output: '00:00:00'
                        }, {
                            input: '-100:-10',
                            output: '00:00:00'
                        }, {
                            input: '99:99',
                            output: '01:40:39'
                        }, {
                            input: '2',
                            output: '00:00:02'
                        }, {
                            input: '1:2',
                            output: '00:01:02'
                        }, {
                            input: '1:25',
                            output: '00:01:25'
                        }, {
                            input: '3:1:25',
                            output: '03:01:25'
                        }, {
                            input: ' 2 3 : 5 9 : 5 9 ',
                            output: '23:59:59'
                        }, {
                            input: '9:1:25',
                            output: '09:01:25'
                        }, {
                            input: '77:72:77',
                            output: '23:59:59'
                        }, {
                            input: '22:100:100',
                            output: '23:41:40'
                        }, {
                            input: '-22:22:22',
                            output: '00:22:22'
                        }, {
                            input: 'simple text',
                            output: '00:00:00'
                        }, {
                            input: 'a10a:a10a:a10a',
                            output: '00:00:00'
                        }, {
                            input: '',
                            output: '00:00:00'
                        }
                    ];
                    $.each(cases, function(index, data) {
                        expect(view.parseRelativeTime(data.input)).toBe(data.output);
                    });
                });
                it('can update its value in the view', function() {
                    assertCanUpdateView(this.view, '23:59:59');
                    this.view.setValueInEditor('33:59:59');
                    this.view.updateModel();
                    assertValueInView(this.view, '23:59:59');
                });
                it('has a clear method to revert to the model default', function() {
                    assertClear(this.view, '00:00:00');
                });
                it('has an update model method', function() {
                    assertUpdateModel(this.view, '12:12:12', '23:59:59');
                });
            });
            describe('MetadataView.Dict allows the user to enter key-value pairs of strings', function() {
                beforeEach(function() {
                    var dictModel;
                    dictModel = new MetadataModel($.extend(true, {}, dictEntry));
                    this.dictView = new MetadataView.Dict({
                        model: dictModel
                    });
                    this.el = this.dictView.$el;
                    return main();
                });
                it('returns the initial value upon initialization', function() {
                    assertValueInView(this.dictView, {
                        'en': 'English',
                        'ru': 'Русский',
                        'ua': 'Українська',
                        'fr': 'Français'
                    });
                });
                it('updates its value correctly', function() {
                    assertCanUpdateView(this.dictView, {
                        'ru': 'Русский',
                        'ua': 'Українська',
                        'fr': 'Français'
                    });
                });
                it('has a clear method to revert to the model default', function() {
                    this.el.find('.create-setting').click();
                    assertClear(this.dictView, {
                        'en': 'English',
                        'ru': 'Русский'
                    });
                    expect(this.el.find('.create-setting')).not.toHaveClass('is-disabled');
                });
                it('has an update model method', function() {
                    assertUpdateModel(this.dictView, null, {
                        'fr': 'Français'
                    });
                });
                it('can add an entry', function() {
                    expect(_.keys(this.dictView.model.get('value')).length).toEqual(4);
                    this.el.find('.create-setting').click();
                    expect(this.el.find('input.input-key').length).toEqual(5);
                });
                it('can remove an entry', function() {
                    expect(_.keys(this.dictView.model.get('value')).length).toEqual(4);
                    this.el.find('.remove-setting').first().click();
                    expect(_.keys(this.dictView.model.get('value')).length).toEqual(3);
                });
                it('only allows one blank entry at a time', function() {
                    expect(this.el.find('input.input-key').length).toEqual(4);
                    this.el.find('.create-setting').click();
                    this.el.find('.create-setting').click();
                    expect(this.el.find('input.input-key').length).toEqual(5);
                });
                it('only allows unique keys', function() {
                    var data;
                    data = [
                        {
                            expectedValue: {
                                'ru': 'Русский'
                            },
                            initialValue: {
                                'ru': 'Русский'
                            },
                            testValue: {
                                'key': 'ru',
                                'value': ''
                            }
                        }, {
                            expectedValue: {
                                'ru': 'Русский'
                            },
                            initialValue: {
                                'ru': 'Some value'
                            },
                            testValue: {
                                'key': 'ru',
                                'value': 'Русский'
                            }
                        }, {
                            expectedValue: {
                                'ru': 'Русский'
                            },
                            initialValue: {
                                'ru': 'Русский'
                            },
                            testValue: {
                                'key': '',
                                'value': ''
                            }
                        }
                    ];
                    _.each(data, (function(d) {
                        var item;
                        this.dictView.setValueInEditor(d.initialValue);
                        this.dictView.updateModel();
                        this.el.find('.create-setting').click();
                        item = this.el.find('.list-settings-item').last();
                        item.find('.input-key').val(d.testValue.key);
                        item.find('.input-value').val(d.testValue.value);
                        expect(this.dictView.getValueFromEditor()).toEqual(d.expectedValue);
                    }).bind(this));
                });
                it('re-enables the add setting button after entering a new value', function() {
                    expect(this.el.find('input.input-key').length).toEqual(4);
                    this.el.find('.create-setting').click();
                    expect(this.el.find('.create-setting')).toHaveClass('is-disabled');
                    this.el.find('input.input-key').last().val('third setting');
                    this.el.find('input.input-key').last().trigger('input');
                    expect(this.el.find('.create-setting')).not.toHaveClass('is-disabled');
                });
            });
        });
    });
}).call(this);
