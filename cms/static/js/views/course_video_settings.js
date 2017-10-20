/**
 * CourseVideoSettingsView shows a sidebar containing course wide video settings which we show on Video Uploads page.
 */
define([
    'jquery', 'backbone', 'underscore', 'gettext', 'moment',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/course-video-settings.underscore'
],
function($, Backbone, _, gettext, moment, HtmlUtils, StringUtils, TranscriptSettingsTemplate) {
    'use strict';

    var CourseVideoSettingsView,
        CIELO24 = 'Cielo24',
        THREE_PLAY_MEDIA = '3PlayMedia';

    CourseVideoSettingsView = Backbone.View.extend({
        el: 'div.video-transcript-settings-wrapper',

        events: {
            'change .transcript-provider-group input': 'providerSelected',
            'change #transcript-turnaround': 'turnaroundSelected',
            'change #transcript-fidelity': 'fidelitySelected',
            'change #video-source-language': 'videoSourceLanguageSelected',
            'click .action-add-language': 'languageSelected',
            'click .action-remove-language': 'languageRemoved',
            'click .action-update-course-video-settings': 'updateCourseVideoSettings',
            'click .action-close-course-video-settings': 'closeCourseVideoSettings'
        },

        initialize: function(options) {
            var videoTranscriptSettings = options.videoTranscriptSettings;
            this.activeTranscriptionPlan = options.activeTranscriptPreferences;
            this.availableTranscriptionPlans = videoTranscriptSettings.transcription_plans;
            this.transcriptHandlerUrl = videoTranscriptSettings.transcript_preferences_handler_url;
            this.template = HtmlUtils.template(TranscriptSettingsTemplate);
            this.setActiveTranscriptPlanData();
            this.selectedLanguages = [];
        },

        registerCloseClickHandler: function() {
            var self = this;

            // Preventing any parent handlers from being notified of the event. This is to stop from firing the document
            // level click handler to execute on course video settings pane click.
            self.$el.click(function(event) {
                event.stopPropagation();
            });

            // Click anywhere outside the course video settings pane would close the pane.
            $(document).click(function(event) {
                // if the target of the click isn't the container nor a descendant of the contain
                if (!self.$el.is(event.target) && self.$el.has(event.target).length === 0) {
                    self.closeCourseVideoSettings();
                }
            });
        },

        resetPlanData: function() {
            this.selectedProvider = '';
            this.selectedTurnaroundPlan = '';
            this.selectedFidelityPlan = '';
            this.activeLanguages = [];
            this.selectedVideoSourceLanguage = '';
            this.selectedLanguages = [];
        },

        setActiveTranscriptPlanData: function() {
            if (this.activeTranscriptionPlan) {
                this.selectedProvider = this.activeTranscriptionPlan.provider;
                this.selectedFidelityPlan = this.activeTranscriptionPlan.cielo24_fidelity;
                this.selectedTurnaroundPlan = this.selectedProvider === CIELO24 ?
                    this.activeTranscriptionPlan.cielo24_turnaround :
                    this.activeTranscriptionPlan.three_play_turnaround;
                this.activeLanguages = this.activeTranscriptionPlan.preferred_languages;
                this.selectedVideoSourceLanguage = this.activeTranscriptionPlan.video_source_language;
            } else {
                this.resetPlanData();
            }
        },

        getTurnaroundPlan: function() {
            var turnaroundPlan = null;
            if (this.selectedProvider) {
                turnaroundPlan = this.availableTranscriptionPlans[this.selectedProvider].turnaround;
            }
            return turnaroundPlan;
        },

        getFidelityPlan: function() {
            var fidelityPlan = null;
            if (this.selectedProvider === CIELO24) {
                fidelityPlan = this.availableTranscriptionPlans[this.selectedProvider].fidelity;
            }
            return fidelityPlan;
        },

        getTargetLanguages: function() {
            var availableLanguages,
                selectedPlan = this.selectedProvider ? this.availableTranscriptionPlans[this.selectedProvider] : null;
            if (selectedPlan) {
                if (this.selectedProvider === CIELO24 && this.selectedFidelityPlan) {
                    availableLanguages = selectedPlan.fidelity[this.selectedFidelityPlan].languages;
                    // If fidelity is mechanical then target language would be same as source language.
                    if (this.selectedFidelityPlan === 'MECHANICAL' && this.selectedVideoSourceLanguage) {
                        availableLanguages = _.pick(
                            availableLanguages,
                            this.selectedVideoSourceLanguage
                        );
                    }
                } else if (this.selectedProvider === THREE_PLAY_MEDIA) {
                    availableLanguages = selectedPlan.languages;
                }
            }
            return availableLanguages;
        },

        getSourceLanguages: function() {
            var sourceLanguages = [];
            if (this.selectedProvider === THREE_PLAY_MEDIA) {
                sourceLanguages = this.availableTranscriptionPlans[this.selectedProvider].translations;
            } else {
                sourceLanguages = this.getTargetLanguages();
            }
            return sourceLanguages;
        },

        fidelitySelected: function(event) {
            var $fidelityContainer = this.$el.find('.transcript-fidelity-wrapper');
            this.selectedFidelityPlan = event.target.value;
            // Remove any error if present already.
            this.clearPreferenceErrorState($fidelityContainer);

            // Clear active and selected languages.
            this.selectedLanguages = this.activeLanguages = [];
            // Also clear selected language.
            this.selectedVideoSourceLanguage = '';
            this.renderSourceLanguages();
            this.renderTargetLanguages();
        },

        videoSourceLanguageSelected: function(event) {
            var $videoSourceLanguageContainer = this.$el.find('.video-source-language-wrapper');
            this.selectedVideoSourceLanguage = event.target.value;
            // Remove any error if present already.
            this.clearPreferenceErrorState($videoSourceLanguageContainer);

            // Clear active and selected languages.
            this.selectedLanguages = this.activeLanguages = [];
            this.renderTargetLanguages();
        },

        turnaroundSelected: function(event) {
            var $turnaroundContainer = this.$el.find('.transcript-turnaround-wrapper');
            this.selectedTurnaroundPlan = event.target.value;
            // Remove any error if present already.
            this.clearPreferenceErrorState($turnaroundContainer);
        },

        providerSelected: function(event) {
            this.resetPlanData();
            this.selectedProvider = event.target.value;
            this.renderPreferences();
        },

        languageSelected: function(event) {
            var $parentEl = $(event.target.parentElement).parent(),
                $languagesEl = this.$el.find('.transcript-languages-wrapper'),
                selectedLanguage = $parentEl.find('select').val();

            // Remove any error if present already.
            this.clearPreferenceErrorState($languagesEl);

            // Only add if not in the list already.
            if (selectedLanguage && _.indexOf(this.selectedLanguages, selectedLanguage) === -1) {
                this.selectedLanguages.push(selectedLanguage);
                this.addLanguage(selectedLanguage);
                // Populate language menu with latest data.
                this.populateLanguageMenu();
            } else {
                this.addErrorState($languagesEl);
            }
        },

        languageRemoved: function(event) {
            var selectedLanguage = $(event.target).data('language-code');
            $(event.target.parentElement).parent().remove();

            // Remove language from selected languages.
            this.selectedLanguages = _.without(this.selectedLanguages, selectedLanguage);

            // Populate menu again to reflect latest changes.
            this.populateLanguageMenu();
        },

        renderProviders: function() {
            var self = this,
                providerPlan = self.availableTranscriptionPlans,
                $providerEl = self.$el.find('.transcript-provider-group');

            if (providerPlan) {
                HtmlUtils.setHtml(
                    $providerEl,
                    HtmlUtils.interpolateHtml(
                        HtmlUtils.HTML('<input type="radio" id="transcript-provider-none" name="transcript-provider" value="" {checked}/><label for="transcript-provider-none">{text}</label>'),    // eslint-disable-line max-len
                        {
                            text: gettext('N/A'),
                            checked: self.selectedProvider === '' ? 'checked' : ''
                        }
                    )
                );

                _.each(providerPlan, function(providerObject, key) {
                    var checked = self.selectedProvider === key ? 'checked' : '';
                    HtmlUtils.append(
                        $providerEl,
                        HtmlUtils.interpolateHtml(
                            HtmlUtils.HTML('<input type="radio" id="transcript-provider-{value}" name="transcript-provider" value="{value}" {checked}/><label for="transcript-provider-{value}">{text}'),   // eslint-disable-line max-len
                            {
                                text: providerObject.display_name,
                                value: key,
                                checked: checked
                            }
                        )
                    );
                });
            }
        },

        renderTurnaround: function() {
            var self = this,
                turnaroundPlan = self.getTurnaroundPlan(),
                $turnaroundContainer = self.$el.find('.transcript-turnaround-wrapper'),
                $turnaround = self.$el.find('#transcript-turnaround');

            // Clear error state if present any.
            this.clearPreferenceErrorState($turnaroundContainer);

            if (turnaroundPlan) {
                HtmlUtils.setHtml(
                    $turnaround,
                    HtmlUtils.HTML(new Option(gettext('Select turnaround'), ''))
                 );
                _.each(turnaroundPlan, function(value, key) {
                    var option = new Option(value, key);
                    if (self.selectedTurnaroundPlan === key) {
                        option.selected = true;
                    }
                    HtmlUtils.append($turnaround, HtmlUtils.HTML(option));
                });
                $turnaroundContainer.show();
            } else {
                $turnaroundContainer.hide();
            }
        },

        renderFidelity: function() {
            var self = this,
                fidelityPlan = self.getFidelityPlan(),
                $fidelityContainer = self.$el.find('.transcript-fidelity-wrapper'),
                $fidelity = self.$el.find('#transcript-fidelity');

            // Clear error state if present any.
            this.clearPreferenceErrorState($fidelityContainer);

            // Fidelity dropdown
            if (fidelityPlan) {
                HtmlUtils.setHtml(
                    $fidelity,
                    HtmlUtils.HTML(new Option(gettext('Select fidelity'), ''))
                );
                _.each(fidelityPlan, function(fidelityObject, key) {
                    var option = new Option(fidelityObject.display_name, key);
                    if (self.selectedFidelityPlan === key) {
                        option.selected = true;
                    }
                    HtmlUtils.append($fidelity, HtmlUtils.HTML(option));
                });
                $fidelityContainer.show();
            } else {
                $fidelityContainer.hide();
            }
        },

        renderTargetLanguages: function() {
            var self = this,
                $languagesPreferenceContainer = self.$el.find('.transcript-languages-wrapper'),
                $languagesContainer = self.$el.find('.languages-container');

            // Clear error state if present any.
            self.clearPreferenceErrorState($languagesPreferenceContainer);

            $languagesContainer.empty();

            // Show language container if source language is selected .
            if (self.selectedVideoSourceLanguage) {
                _.each(self.activeLanguages, function(language) {
                    // Only add if not in the list already.
                    if (_.indexOf(self.selectedLanguages, language) === -1) {
                        self.selectedLanguages.push(language);
                    }
                    // Show active/ add language language container
                    self.addLanguage(language);
                });
                $languagesPreferenceContainer.show();
                self.populateLanguageMenu();
            } else {
                $languagesPreferenceContainer.hide();
            }
        },

        renderSourceLanguages: function() {
            var self = this,
                availableLanguages = self.getTargetLanguages(),
                availableTranslations = self.getSourceLanguages(),
                $videoSourceLanguageContainer = self.$el.find('.video-source-language-wrapper'),
                $languageMenuEl = self.$el.find('.video-source-language'),
                selectOptionEl = new Option(gettext('Select language'), '');

            // Clear error state if present any.
            self.clearPreferenceErrorState($videoSourceLanguageContainer);

            if (!_.isEmpty(availableTranslations)) {
                $videoSourceLanguageContainer.show();

                // We need to set id due to a11y aria-labelledby
                selectOptionEl.id = 'video-source-language-none';

                HtmlUtils.setHtml(
                    $languageMenuEl,
                    HtmlUtils.HTML(selectOptionEl)
                );

                _.each(availableTranslations, function(translatableLanguage, key) {
                    var option = new Option(availableLanguages[key], key);
                    if (self.selectedVideoSourceLanguage === key) {
                        option.selected = true;
                    }
                    HtmlUtils.append(
                        $languageMenuEl,
                        HtmlUtils.HTML(option)
                    );
                });
            } else {
                $videoSourceLanguageContainer.hide();
            }
        },

        populateLanguageMenu: function() {
            var availableLanguages = this.getTargetLanguages(),
                availableTranslations = this.availableTranscriptionPlans[THREE_PLAY_MEDIA].translations,
                $languageMenuEl = this.$el.find('.transcript-language-menu'),
                $languageMenuContainerEl = this.$el.find('.transcript-language-menu-container'),
                selectOptionEl = new Option(gettext('Select language'), '');

            if (this.selectedProvider === THREE_PLAY_MEDIA) {
                // Pick out only those languages from plan laguages that also come from video source language.
                availableLanguages = _.pick(
                    availableLanguages,
                    availableTranslations[this.selectedVideoSourceLanguage]
                );
            }

            // Omit out selected languages from selecting again.
            availableLanguages = _.omit(availableLanguages, this.selectedLanguages);

            // If no available language is left, then don't even show add language box.
            if (_.keys(availableLanguages).length) {
                $languageMenuContainerEl.show();
                // We need to set id due to a11y aria-labelledby
                selectOptionEl.id = 'transcript-language-none';

                HtmlUtils.setHtml(
                    $languageMenuEl,
                    HtmlUtils.HTML(selectOptionEl)
                );

                _.each(availableLanguages, function(value, key) {
                    HtmlUtils.append(
                        $languageMenuEl,
                        HtmlUtils.HTML(new Option(value, key))
                    );
                });
            } else {
                $languageMenuContainerEl.hide();
            }
        },

        renderPreferences: function() {
            this.renderProviders();
            this.renderTurnaround();
            this.renderFidelity();
            this.renderSourceLanguages();
            this.renderTargetLanguages();
        },

        addLanguage: function(language) {
            var $languagesContainer = this.$el.find('.languages-container');
            HtmlUtils.append(
                $languagesContainer,
                HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<div class="transcript-language-container">'),
                    HtmlUtils.interpolateHtml(
                        HtmlUtils.HTML('<span>{languageDisplayName}</span>'),
                        {
                            languageDisplayName: this.getTargetLanguages()[language]
                        }
                    ),
                    HtmlUtils.interpolateHtml(
                        HtmlUtils.HTML('<div class="remove-language-action"><button class="button-link action-remove-language" data-language-code="{languageCode}">{text}<span class="sr">{srText}</span></button></div>'), // eslint-disable-line max-len
                        {
                            languageCode: language,
                            text: gettext('Remove'),
                            srText: gettext('Press Remove to remove language')
                        }
                    ),
                    HtmlUtils.HTML('</div>')
                )
            );
        },

        updateSuccessResponseStatus: function(data) {
            var dateModified = data ? moment.utc(data.modified).format('ll') : '';

            // Update last modified date
            if (dateModified) {
                HtmlUtils.setHtml(
                    this.$el.find('.last-updated-text'),
                    HtmlUtils.interpolateHtml(
                        HtmlUtils.HTML('{lastUpdateText} {dateModified}'),
                        {
                            lastUpdateText: gettext('Last updated'),
                            dateModified: dateModified
                        }
                    )
                );
            }

            this.renderResponseStatus(gettext('Settings updated'), 'success');
            // Sync ActiveUploadListView with latest active plan.
            this.activeTranscriptionPlan = data;
            Backbone.trigger('coursevideosettings:syncActiveTranscriptPreferences', this.activeTranscriptionPlan);
        },

        updateFailResponseStatus: function(data) {
            var errorMessage;
            // Enclose inside try-catch so that if we get erroneous data, we could still
            // show some error to user
            try {
                errorMessage = $.parseJSON(data).error;
            } catch (e) {}  // eslint-disable-line no-empty
            errorMessage = errorMessage || gettext('Error saving data');
            this.renderResponseStatus(errorMessage, 'error');
        },

        renderResponseStatus: function(responseText, type) {
            var addClass = type === 'error' ? 'error' : 'success',
                removeClass = type === 'error' ? 'success' : 'error',
                iconClass = type === 'error' ? 'fa-info-circle' : 'fa-check-circle',
                $messageWrapperEl = this.$el.find('.course-video-settings-message-wrapper');
            $messageWrapperEl.removeClass(removeClass);
            $messageWrapperEl.addClass(addClass);
            HtmlUtils.setHtml(
                $messageWrapperEl,
                HtmlUtils.interpolateHtml(
                    HtmlUtils.HTML('<div class="course-video-settings-message"><span class="icon fa {iconClass}" aria-hidden="true"></span><span>{text}</span></div>'), // eslint-disable-line max-len
                    {
                        text: responseText,
                        iconClass: iconClass
                    }
                )
            );
        },

        clearResponseStatus: function() {
            // Remove parent level state.
            var $messageWrapperEl = this.$el.find('.course-video-settings-message-wrapper');
            $messageWrapperEl.empty();
            $messageWrapperEl.removeClass('error');
            $messageWrapperEl.removeClass('success');
        },

        clearPreferenceErrorState: function($PreferenceContainer) {
            $PreferenceContainer.removeClass('error');
            $PreferenceContainer.find('.error-icon').empty();
            $PreferenceContainer.find('.error-info').empty();

            // Also clear response status if present already
            this.clearResponseStatus();
        },

        addErrorState: function($PreferenceContainer) {
            var requiredText = gettext('Required'),
                infoIconHtml = HtmlUtils.HTML('<span class="icon fa fa-info-circle" aria-hidden="true"></span>');

            $PreferenceContainer.addClass('error');
            HtmlUtils.setHtml(
                $PreferenceContainer.find('.error-icon'),
                infoIconHtml
            );
            HtmlUtils.setHtml(
                $PreferenceContainer.find('.error-info'),
                requiredText
            );
        },

        validateCourseVideoSettings: function() {
            var isValid = true,
                $turnaroundEl = this.$el.find('.transcript-turnaround-wrapper'),
                $fidelityEl = this.$el.find('.transcript-fidelity-wrapper'),
                $languagesEl = this.$el.find('.transcript-languages-wrapper'),
                $videoSourcelanguageEl = this.$el.find('.video-source-language-wrapper');


            // Explicit None selected case.
            if (this.selectedProvider === '') {
                return true;
            }

            if (!this.selectedTurnaroundPlan) {
                isValid = false;
                this.addErrorState($turnaroundEl);
            } else {
                this.clearPreferenceErrorState($turnaroundEl);
            }

            if (this.selectedProvider === CIELO24 && !this.selectedFidelityPlan) {
                isValid = false;
                this.addErrorState($fidelityEl);
            } else {
                this.clearPreferenceErrorState($fidelityEl);
            }

            if (this.selectedProvider === THREE_PLAY_MEDIA && !this.selectedVideoSourceLanguage) {
                isValid = false;
                this.addErrorState($videoSourcelanguageEl);
            } else {
                this.clearPreferenceErrorState($videoSourcelanguageEl);
            }

            if (this.selectedLanguages.length === 0) {
                isValid = false;
                this.addErrorState($languagesEl);
            } else {
                this.clearPreferenceErrorState($languagesEl);
            }

            return isValid;
        },

        saveTranscriptPreferences: function() {
            var self = this,
                responseTranscriptPreferences;
            // First clear response status if present already
            this.clearResponseStatus();

            if (self.selectedProvider) {
                $.postJSON(self.transcriptHandlerUrl, {
                    provider: self.selectedProvider,
                    cielo24_fidelity: self.selectedFidelityPlan,
                    cielo24_turnaround: self.selectedProvider === CIELO24 ? self.selectedTurnaroundPlan : '',
                    three_play_turnaround: self.selectedProvider === THREE_PLAY_MEDIA ? self.selectedTurnaroundPlan : '',   // eslint-disable-line max-len
                    preferred_languages: self.selectedLanguages,
                    video_source_language: self.selectedVideoSourceLanguage,
                    global: false   // Do not trigger global AJAX error handler
                }, function(data) {
                    responseTranscriptPreferences = data ? data.transcript_preferences : null;
                    self.updateSuccessResponseStatus(responseTranscriptPreferences);
                }).fail(function(jqXHR) {
                    if (jqXHR.responseText) {
                        self.updateFailResponseStatus(jqXHR.responseText);
                    }
                });
            } else {
                $.ajax({
                    type: 'DELETE',
                    url: self.transcriptHandlerUrl
                }).done(function() {
                    self.updateSuccessResponseStatus(null);
                }).fail(function(jqXHR) {
                    if (jqXHR.responseText) {
                        self.updateFailResponseStatus(jqXHR.responseText);
                    }
                });
            }
        },

        updateCourseVideoSettings: function() {
            var $messageWrapperEl = this.$el.find('.course-video-settings-message-wrapper');
            if (this.validateCourseVideoSettings()) {
                this.saveTranscriptPreferences();
            } else {
                $messageWrapperEl.empty();
            }
        },

        render: function() {
            var dateModified = this.activeTranscriptionPlan ?
                moment.utc(this.activeTranscriptionPlan.modified).format('ll') : '';
            HtmlUtils.setHtml(
                this.$el,
                this.template({
                    dateModified: dateModified
                })
            );

            this.renderPreferences();

            this.registerCloseClickHandler();
            this.setFixedCourseVideoSettingsPane();
            return this;
        },

        setFixedCourseVideoSettingsPane: function() {
            var $courseVideoSettingsButton = $('.course-video-settings-button'),
                $courseVideoSettingsContainer = this.$el.find('.course-video-settings-container'),
                initialPositionTop = $courseVideoSettingsContainer.offset().top,
                // Button right position =  width of window - button left position - button width - paddings - border.
                $courseVideoSettingsButtonRight = $(window).width() -
                    $courseVideoSettingsButton.offset().left -
                    $courseVideoSettingsButton.width() -
                    $courseVideoSettingsButton.css('padding-left').replace('px', '') -
                    $courseVideoSettingsButton.css('padding-right').replace('px', '') -
                    $courseVideoSettingsButton.css('border-width').replace('px', '') - 5;   // Extra pixles for slack;

            // Set to windows total height
            $courseVideoSettingsContainer.css('height', $(window).height());

            // Start settings pane adjascent to 'course video settings' button.
            $courseVideoSettingsContainer.css('right', $courseVideoSettingsButtonRight);

            // Make sticky when scroll reaches top.
            $(window).scroll(function() {
                if ($(window).scrollTop() >= initialPositionTop) {
                    $courseVideoSettingsContainer.addClass('fixed-container');
                } else {
                    $courseVideoSettingsContainer.removeClass('fixed-container');
                }
            });
        },

        closeCourseVideoSettings: function() {
            // TODO: Slide out when closing settings pane. We may need to hide the view instead of destroying it.

            // Trigger destroy transcript event.
            Backbone.trigger('coursevideosettings:destroyCourseVideoSettingsView');

            // Unbind any events associated
            this.undelegateEvents();
            this.stopListening();

            // Empty this.$el content from DOM
            this.$el.empty();

            // Reset everything.
            this.resetPlanData();
        }
    });

    return CourseVideoSettingsView;
});
