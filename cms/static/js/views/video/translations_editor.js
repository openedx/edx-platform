define(
    [
        'jquery', 'underscore', 'edx-ui-toolkit/js/utils/html-utils', 'js/views/video/transcripts/utils',
        'js/views/abstract_editor', 'common/js/components/utils/view_utils', 'js/models/uploads', 'js/views/uploads'
    ],
    function($, _, HtmlUtils, TranscriptUtils, AbstractEditor, ViewUtils, FileUpload, UploadDialog) {
        'use strict';

        var VideoUploadDialog = UploadDialog.extend({
            error: function() {
                this.model.set({
                    uploading: false,
                    uploadedBytes: 0,
                    title: gettext('Sorry, there was an error parsing the subtitles that you uploaded. Please check the format and try again.')
                });
            }
        });

        var Translations = AbstractEditor.extend({
            events: {
                'click .create-setting': 'addEntry',
                'click .remove-setting': 'removeEntry',
                'click .upload-setting': 'upload',
                'change select': 'onChangeHandler'
            },

            templateName: 'metadata-translations-entry',
            templateItemName: 'metadata-translations-item',

            validFileFormats: ['srt'],

            initialize: function() {
                var templateName = _.result(this, 'templateItemName'),
                    tpl = document.getElementById(templateName).text,
                    languageMap = {};

                if (!tpl) {
                    console.error("Couldn't load template for item: " + templateName);
                }

                this.templateItem = _.template(tpl);

                // Initialize language map. This maps original language to the newly selected language.
                // Keys in this map represent language codes present on server, they don't change when
                // user selects a language while values represent currently selected language.
                // Initially, the map will look like {'ar': 'ar', 'zh': 'zh'} i.e {'original_lang': 'original_lang'}
                // and corresponding dropdowns will show language names Arabic and Chinese. If user changes
                // Chinese to Russian then map will become {'ar': 'ar', 'zh': 'ru'} i.e {'original_lang': 'new_lang'}
                _.each(this.model.getDisplayValue(), function(value, lang) {
                    languageMap[lang] = lang;
                });
                TranscriptUtils.Storage.set('languageMap', languageMap);
                AbstractEditor.prototype.initialize.apply(this, arguments);
            },

            getDropdown: (function() {
                var dropdown,
                    disableOptions = function(element, values) {
                        var dropdown = $(element).clone();

                        _.each(values, function(value, key) {
                        // Note: IE may raise an exception if key is an empty string,
                        // while other browsers return null as excepted. So coerce it
                        // into null for browser consistency.
                            if (key === '') {
                                key = null;
                            }

                            var option = dropdown[0].options.namedItem(key);

                            if (option) {
                                option.disabled = true;
                            }
                        });

                        return dropdown;
                    };

                return function(values) {
                    if (dropdown) {
                        return disableOptions(dropdown, values);
                    }

                    dropdown = document.createElement('select');
                    dropdown.options.add(new Option());
                    _.each(this.model.get('languages'), function(lang, index) {
                        var option = new Option();

                        option.setAttribute('name', lang.code);
                        option.value = lang.code;
                        option.text = lang.label;
                        dropdown.options.add(option);
                    });

                    return disableOptions(dropdown, values);
                };
            }()),

            getValueFromEditor: function() {
                var dict = {},
                    items = this.$el.find('ol').find('.list-settings-item');

                _.each(items, function(element, index) {
                    var key = $(element).find('select option:selected').val(),
                        value = $(element).find('.input').val();

                    // Keys should be unique, so if our keys are duplicated and
                    // second key is empty or key and value are empty just do
                    // nothing. Otherwise, it'll be overwritten by the new value.
                    if (value === '') {
                        if (key === '' || key in dict) {
                            return false;
                        }
                    }

                    dict[key] = value;
                });

                return dict;
            },

            // @TODO: Use backbone render patterns.
            setValueInEditor: function(values) {
                var self = this,
                    frag = document.createDocumentFragment(),
                    dropdown = self.getDropdown(values),
                    languageMap = TranscriptUtils.Storage.get('languageMap');

                _.each(values, function(value, newLang) {
                    var $html = $(self.templateItem({
                        newLang: newLang,
                        originalLang: _.findKey(languageMap, function(lang) { return lang === newLang; }) || '',
                        value: value,
                        url: self.model.get('urlRoot')
                    }));
                    HtmlUtils.prepend($html, HtmlUtils.HTML(dropdown.clone().val(newLang)));
                    frag.appendChild($html[0]);
                });

                HtmlUtils.setHtml(
                    this.$el.find('ol'),
                    HtmlUtils.HTML([frag])
                );
            },

            addEntry: function(event) {
                event.preventDefault();
                // We don't call updateModel here since it's bound to the
                // change event
                this.setValueInEditor(this.getAllLanguageDropdownElementsData(true));
                this.$el.find('.create-setting').addClass('is-disabled').attr('aria-disabled', true);
            },

            removeEntry: function(event) {
                var self = this,
                    $currentListItemEl = $(event.currentTarget).parent(),
                    originalLang = $currentListItemEl.data('original-lang'),
                    selectedLang = $currentListItemEl.find('select option:selected').val(),
                    languageMap = TranscriptUtils.Storage.get('languageMap'),
                    edxVideoIdField = TranscriptUtils.getField(self.model.collection, 'edx_video_id');

                event.preventDefault();

                /*
            There is a scenario when a user adds an empty video translation item and
            removes it. In such cases, omitting will have no harm on the model
            values or languages map.
            */
                if (originalLang) {
                    ViewUtils.confirmThenRunOperation(
                        gettext('Are you sure you want to remove this transcript?'),
                        gettext('If you remove this transcript, the transcript will not be available for this component.'),
                        gettext('Remove Transcript'),
                        function() {
                            ViewUtils.runOperationShowingMessage(
                                gettext('Removing'),
                                function() {
                                    return $.ajax({
                                        url: self.model.get('urlRoot'),
                                        type: 'DELETE',
                                        data: JSON.stringify({lang: originalLang, edx_video_id: edxVideoIdField.getValue()})
                                    }).done(function() {
                                        self.setValueInEditor(self.getAllLanguageDropdownElementsData(false, selectedLang));
                                        TranscriptUtils.Storage.set('languageMap', _.omit(languageMap, originalLang));
                                    });
                                }
                            );
                        }
                    );
                } else {
                    this.setValueInEditor(this.getAllLanguageDropdownElementsData(false, selectedLang));
                }

                this.$el.find('.create-setting').removeClass('is-disabled').attr('aria-disabled', false);
            },

            upload: function(event) {
                var self = this,
                    $target = $(event.currentTarget),
                    $listItem = $target.parents('li.list-settings-item'),
                    originalLang = $listItem.data('original-lang'),
                    newLang = $listItem.find(':selected').val(),
                    edxVideoIdField = TranscriptUtils.getField(self.model.collection, 'edx_video_id'),
                    fileUploadModel,
                    uploadData,
                    videoUploadDialog;

                event.preventDefault();

                // That's the case when an author is
                // uploading a new transcript.
                if (!originalLang) {
                    originalLang = newLang;
                }

                // Transcript data payload
                uploadData = {
                    edx_video_id: edxVideoIdField.getValue(),
                    language_code: originalLang,
                    new_language_code: newLang
                };

                fileUploadModel = new FileUpload({
                    title: gettext('Upload translation'),
                    fileFormats: this.validFileFormats
                });

                videoUploadDialog = new VideoUploadDialog({
                    model: fileUploadModel,
                    url: this.model.get('urlRoot'),
                    parentElement: $target.closest('.xblock-editor'),
                    uploadData: uploadData,
                    onSuccess: function(response) {
                        var languageMap = TranscriptUtils.Storage.get('languageMap'),
                            newLangObject = {};

                        // new language entry to be added to languageMap
                        newLangObject[newLang] = newLang;

                        // Update edx-video-id
                        edxVideoIdField.setValue(response.edx_video_id);

                        // Update language map by omitting original lang and adding new lang
                        // if languageMap is empty then newLang will be added
                        // if an original lang is replaced with new lang then omit the original lang and the add new lang
                        languageMap = _.extend(_.omit(languageMap, originalLang), newLangObject);
                        TranscriptUtils.Storage.set('languageMap', languageMap);

                        // re-render the whole view
                        self.setValueInEditor(self.getAllLanguageDropdownElementsData());
                    }
                });
                videoUploadDialog.show();
            },

            enableAdd: function() {
                this.$el.find('.create-setting').removeClass('is-disabled').attr('aria-disabled', false);
            },

            onChangeHandler: function(event) {
                var $target = $(event.currentTarget),
                    $listItem = $target.parents('li.list-settings-item'),
                    originalLang = $listItem.data('original-lang'),
                    newLang = $listItem.find('select option:selected').val(),
                    languageMap = TranscriptUtils.Storage.get('languageMap');

                // To protect against any new/unsaved language code in the map.
                if (originalLang in languageMap) {
                    languageMap[originalLang] = newLang;
                    TranscriptUtils.Storage.set('languageMap', languageMap);

                    // an existing saved lang is changed, no need to re-render the whole view
                    return;
                }

                this.enableAdd();
                this.setValueInEditor(this.getAllLanguageDropdownElementsData());
            },

            /**
         * Constructs data extracted from each dropdown. This will be used to re-render the whole view.
         */
            getAllLanguageDropdownElementsData: function(isNew, omittedLanguage) {
                var data = {},
                    languageDropdownElements = this.$el.find('select'),
                    languageMap = TranscriptUtils.Storage.get('languageMap');

                // data object will mirror the languageMap. `data` will contain lang to lang map as explained below
                // {originalLang: originalLang};            original lang not changed
                // {newLang: originalLang};                 original lang changed to a new lang
                // {selectedLang: ''};                      new lang to be added, no entry in languageMap
                _.each(languageDropdownElements, function(languageDropdown) {
                    var language = $(languageDropdown).find(':selected').val();
                    data[language] = _.findKey(languageMap, function(lang) { return lang === language; }) || '';
                });

                // This is needed to render an empty item that
                // will be further used to upload a transcript.
                if (isNew) {
                    data[''] = '';
                }

                // This Omits a language from the dropdown's data. It is
                // needed when an item is going to be removed.
                if (typeof(omittedLanguage) !== 'undefined') {
                    data = _.omit(data, omittedLanguage);
                }

                return data;
            }
        });

        return Translations;
    });
