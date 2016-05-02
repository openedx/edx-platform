define(
    [
        'jquery', 'underscore', 'squire'
    ],
function ($, _, Squire) {
    'use strict';
    // TODO: fix BLD-1100 Disabled due to intermittent failure on master and in PR builds
    xdescribe('VideoTranslations', function () {
        var TranslationsEntryTemplate = readFixtures(
                'video/metadata-translations-entry.underscore'
            ),
            TranslationsItenTemplate = readFixtures(
                'video/metadata-translations-item.underscore'
            ),
            modelStub = {
                default_value: {
                    'en': 'en.srt',
                    'ru': 'ru.srt'
                },
                display_name: 'Transcript Translation',
                explicitly_set: false,
                field_name: 'translations',
                help: 'Specifies the name for this component.',
                type: 'VideoTranslations',
                languages: [
                    {code: 'zh', label: 'Chinese'},
                    {code: 'en', label: 'English'},
                    {code: 'fr', label: 'French'},
                    {code: 'ru', label: 'Russian'},
                    {code: 'uk', label: 'Ukrainian'}
                ],
                value: {
                    'en': 'en.srt',
                    'ru': 'ru.srt',
                    'uk': 'uk.srt',
                    'fr': 'fr.srt'
                }
            },
            self, injector;

        var setValue = function (view, value) {
            view.setValueInEditor(value);
            view.updateModel();
        };

        var createPromptSpy = function (name) {
            var spy = jasmine.createSpyObj(name, ['constructor', 'show', 'hide']);
            spy.constructor.andReturn(spy);
            spy.show.andReturn(spy);
            spy.extend = jasmine.createSpy().andReturn(spy.constructor);

            return spy;
        };

        beforeEach(function () {
            self = this;

            this.addMatchers({
                assertValueInView: function(expected) {
                    var value = this.actual.getValueFromEditor();
                    return this.env.equals_(value, expected);
                },
                assertCanUpdateView: function (expected) {
                    var view = this.actual,
                        value;

                    view.setValueInEditor(expected);
                    value = view.getValueFromEditor();

                    return this.env.equals_(value, expected);
                },
                assertClear: function (modelValue) {
                    var env = this.env,
                        view = this.actual,
                        model = view.model;

                    return model.getValue() === null &&
                           env.equals_(model.getDisplayValue(), modelValue) &&
                           env.equals_(view.getValueFromEditor(), modelValue);
                },
                assertUpdateModel: function (originalValue, newValue) {
                    var env = this.env,
                        view = this.actual,
                        model = view.model,
                        expectOriginal;

                    view.setValueInEditor(newValue);
                    expectOriginal = env.equals_(model.getValue(), originalValue);
                    view.updateModel();

                    return expectOriginal &&
                           env.equals_(model.getValue(), newValue);
                },
                verifyKeysUnique: function (initial, expected, testData) {
                    var env = this.env,
                        view = this.actual,
                        item, value;

                    view.setValueInEditor(initial);
                    view.updateModel();
                    view.$el.find('.create-setting').click();
                    item = view.$el.find('.list-settings-item').last();
                    item.find('select').val(testData.key);
                    item.find('input:hidden').val(testData.value);
                    value = view.getValueFromEditor();

                    return env.equals_(value, expected);
                },
                verifyButtons: function (upload, download, remove, index) {
                    var view = this.actual,
                        items = view.$el.find('.list-settings-item'),
                        item  = index ? items.eq(index) : items.last(),
                        uploadBtn = item.find('.upload-setting'),
                        downloadBtn = item.find('.download-setting'),
                        removeBtn = item.find('.remove-setting');


                    upload = upload ? uploadBtn.length : !uploadBtn.length;
                    download = download ? downloadBtn.length : !downloadBtn.length;
                    remove = remove ? removeBtn.length : !removeBtn.length;

                    return upload && download && remove;

                }
            });

            appendSetFixtures($('<script>', {
                id: 'metadata-translations-entry',
                type: 'text/template'
            }).text(TranslationsEntryTemplate));

            appendSetFixtures($('<script>', {
                id: 'metadata-translations-item',
                type: 'text/template'
            }).text(TranslationsItenTemplate));

            this.uploadSpies = createPromptSpy('UploadDialog');

            injector = new Squire();
            injector.mock('js/views/uploads', function () {
                return self.uploadSpies;
            });

            runs(function() {
                injector.require([
                    'js/models/metadata', 'js/views/video/translations_editor'
                ],
                function(MetadataModel, Translations) {
                    var model = new MetadataModel($.extend(true, {}, modelStub));
                    self.view = new Translations({model: model});
                });
            });

            waitsFor(function() {
                return self.view;
            }, 'VideoTranslations was not created', 1000);
        });

        afterEach(function () {
            injector.clean();
            injector.remove();
        });

        it('returns the initial value upon initialization', function () {
            expect(this.view).assertValueInView({
                'en': 'en.srt',
                'ru': 'ru.srt',
                'uk': 'uk.srt',
                'fr': 'fr.srt'
            });

            expect(this.view).verifyButtons(true, true, true);
        });

        it('updates its value correctly', function () {
            expect(this.view).assertCanUpdateView({
                'ru': 'ru.srt',
                'uk': 'uk.srt',
                'fr': 'fr.srt'
            });
        });

        it('upload works correctly', function () {
            var options;

            setValue(this.view, {
                'en': 'en.srt',
                'ru': 'ru.srt',
                'uk': 'uk.srt',
                'fr': 'fr.srt',
                'zh': ''
            });

            expect(this.view).verifyButtons(true, false, true);

            this.view.$el.find('.upload-setting').last().click();

            expect(this.uploadSpies.constructor).toHaveBeenCalled();
            expect(this.uploadSpies.show).toHaveBeenCalled();

            options = this.uploadSpies.constructor.mostRecentCall.args[0];
            options.onSuccess({'filename': 'zh.srt'});

            expect(this.view).verifyButtons(true, true, true);

            expect(this.view.getValueFromEditor()).toEqual({
                'en': 'en.srt',
                'ru': 'ru.srt',
                'uk': 'uk.srt',
                'fr': 'fr.srt',
                'zh': 'zh.srt'
            });
        });

        it('has a clear method to revert to the model default', function () {
            setValue(this.view, {
                'fr': 'en.srt',
                'uk': 'ru.srt'
            });

            this.view.$el.find('.create-setting').click();

            this.view.clear();

            expect(this.view).assertClear({
                'en': 'en.srt',
                'ru': 'ru.srt'
            });

            expect(this.view.$el.find('.create-setting')).not.toHaveClass('is-disabled');
        });

        it('has an update model method', function () {
            expect(this.view).assertUpdateModel(null, {'fr': 'fr.srt'});
        });

        it('can add an entry', function () {
            expect(_.keys(this.view.model.get('value')).length).toEqual(4);
            this.view.$el.find('.create-setting').click();
            expect(this.view.$el.find('select').length).toEqual(5);
        });

        it('can remove an entry', function () {
            setValue(this.view, {
                'en': 'en.srt',
                'ru': 'ru.srt',
                'fr': ''
            });
            expect(_.keys(this.view.model.get('value')).length).toEqual(3);
            this.view.$el.find('.remove-setting').last().click();
            expect(_.keys(this.view.model.get('value')).length).toEqual(2);
        });

        it('only allows one blank entry at a time', function () {
            expect(this.view.$el.find('select').length).toEqual(4);
            this.view.$el.find('.create-setting').click();
            this.view.$el.find('.create-setting').click();
            expect(this.view.$el.find('select').length).toEqual(5);
        });

        it('only allows unique keys', function () {
            expect(this.view).verifyKeysUnique(
                {'ru': 'ru.srt'}, {'ru': 'ru.srt'}, {'key': 'ru', 'value': ''}
            );

            expect(this.view).verifyKeysUnique(
                {'ru': 'en.srt'}, {'ru': 'ru.srt'}, {'key': 'ru', 'value': 'ru.srt'}
            );

            expect(this.view).verifyKeysUnique(
                {'ru': 'ru.srt'}, {'ru': 'ru.srt'}, {'key': '', 'value': ''}
            );
        });

        it('re-enables the add setting button after entering a new value', function () {
            expect(this.view.$el.find('select').length).toEqual(4);
            this.view.$el.find('.create-setting').click();
            expect(this.view).verifyButtons(false, false, true);
            expect(this.view.$el.find('.create-setting')).toHaveClass('is-disabled');
            this.view.$el.find('select').last().val('zh');
            this.view.$el.find('select').last().trigger('change');
            expect(this.view).verifyButtons(true, false, true);
            expect(this.view.$el.find('.create-setting')).not.toHaveClass('is-disabled');
        });
    });
});
